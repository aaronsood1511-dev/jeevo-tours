import Foundation
import CoreGraphics
import ImageIO
import UniformTypeIdentifiers

// prep <in> <out> <bleedPx> <texX0,texY0,texX1,texY1> <patch:x0,y0,x1,y1> ...
// Erases each patch rect by interpolating the cream vertically between the
// rows just outside it, then lays the real paper grain from the texture rect
// back over the top so the repair does not read as a flat sticker.
let A = CommandLine.arguments
func nums(_ s: String) -> [Int] { s.split(separator: ",").map { Int($0)! } }

let src = URL(fileURLWithPath: A[1]) as CFURL
guard let isrc = CGImageSourceCreateWithURL(src, nil),
      let cg = CGImageSourceCreateImageAtIndex(isrc, 0, nil) else { exit(1) }
let W = cg.width, H = cg.height
var buf = [UInt8](repeating: 0, count: W*H*4)
let cs = CGColorSpaceCreateDeviceRGB()
let bi = CGImageAlphaInfo.premultipliedLast.rawValue
var ctx = CGContext(data: &buf, width: W, height: H, bitsPerComponent: 8,
                    bytesPerRow: W*4, space: cs, bitmapInfo: bi)!
ctx.draw(cg, in: CGRect(x: 0, y: 0, width: W, height: H))
@inline(__always) func idx(_ x: Int, _ y: Int) -> Int { (y*W + x)*4 }

let bleed = Int(A[3])!
let tex = nums(A[4])                              // x0,y0,x1,y1
let tW = tex[2]-tex[0], tH = tex[3]-tex[1]

// per-column smooth model of the texture patch, so we can isolate its grain
var texLow = [Double](repeating: 0, count: tW*tH*3)
let K = 9
for c in 0..<3 {
    for ty in 0..<tH {
        for tx in 0..<tW {
            var s = 0.0, n = 0.0
            for dy in -K...K { for dx in -K...K {
                let sx = min(max(tx+dx, 0), tW-1), sy = min(max(ty+dy, 0), tH-1)
                s += Double(buf[idx(tex[0]+sx, tex[1]+sy) + c]); n += 1
            }}
            texLow[(ty*tW + tx)*3 + c] = s/n
        }
    }
}

func blur1(_ a: [Double], _ r: Int) -> [Double] {
    var o = a
    for i in 0..<a.count {
        var s = 0.0, n = 0.0
        for d in -r...r { let j = min(max(i+d, 0), a.count-1); s += a[j]; n += 1 }
        o[i] = s/n
    }
    return o
}

for ai in 5..<A.count {
    let p = nums(A[ai])
    let x0 = p[0], y0 = p[1], x1 = p[2], y1 = p[3]
    let band = 9, feather = 5
    for c in 0..<3 {
        // average a band just above and just below the hole
        var top = [Double](repeating: 0, count: x1-x0)
        var bot = top
        for x in x0..<x1 {
            var st = 0.0, sb = 0.0
            for k in 1...band {
                st += Double(buf[idx(x, max(y0-k, 0)) + c])
                sb += Double(buf[idx(x, min(y1+k, H-1)) + c])
            }
            top[x-x0] = st/Double(band); bot[x-x0] = sb/Double(band)
        }
        top = blur1(top, 14); bot = blur1(bot, 14)
        for y in y0..<y1 {
            let t = Double(y-y0) / Double(max(y1-y0-1, 1))
            for x in x0..<x1 {
                let base = top[x-x0]*(1-t) + bot[x-x0]*t
                // mirror-tile the grain so there is no repeat seam
                var gx = (x - x0) % (tW*2); if gx >= tW { gx = tW*2 - 1 - gx }
                var gy = (y - y0) % (tH*2); if gy >= tH { gy = tH*2 - 1 - gy }
                let grain = Double(buf[idx(tex[0]+gx, tex[1]+gy) + c]) - texLow[(gy*tW + gx)*3 + c]
                var v = base + grain
                // feather the join so the repair has no hard border
                let d = min(min(x-x0, x1-1-x), min(y-y0, y1-1-y))
                if d < feather {
                    let w = Double(d+1)/Double(feather+1)
                    v = v*w + Double(buf[idx(x, y) + c])*(1-w)
                }
                buf[idx(x, y) + c] = UInt8(min(max(v, 0), 255))
            }
        }
    }
}

// Grow the card into its bleed by replicating its edge. The outermost pixel
// of the rectified card is an antialiased transition against the mockup's
// background, so sample from INSET in - otherwise that dirty pixel becomes a
// 3mm halo all the way round.
let INSET = 3
let OW = W + bleed*2, OH = H + bleed*2
var out = [UInt8](repeating: 255, count: OW*OH*4)
@inline(__always) func oidx(_ x: Int, _ y: Int) -> Int { (y*OW + x)*4 }
for y in 0..<OH {
    let sy = min(max(y - bleed, INSET), H-1-INSET)
    for x in 0..<OW {
        let sx = min(max(x - bleed, INSET), W-1-INSET)
        for c in 0..<4 { out[oidx(x, y)+c] = buf[idx(sx, sy)+c] }
    }
}
let octx = CGContext(data: &out, width: OW, height: OH, bitsPerComponent: 8,
                     bytesPerRow: OW*4, space: cs, bitmapInfo: bi)!
guard let img = octx.makeImage() else { exit(2) }
let dst = URL(fileURLWithPath: A[2]) as CFURL
if let d = CGImageDestinationCreateWithURL(dst, UTType.png.identifier as CFString, 1, nil) {
    CGImageDestinationAddImage(d, img, nil); CGImageDestinationFinalize(d)
}
print("wrote \(A[2]) \(OW)x\(OH)")
