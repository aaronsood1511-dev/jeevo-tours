import Foundation
import CoreGraphics
import ImageIO
import CoreImage
import UniformTypeIdentifiers

// rectify <src> <out> <W> <H> <tlx,tly> <trx,try> <brx,bry> <blx,bly>
// corner points are in TOP-LEFT origin pixel coords of <src>
let a = CommandLine.arguments
func pt(_ s: String, _ h: CGFloat) -> CGPoint {
    let c = s.split(separator: ",").map { CGFloat(Double($0)!) }
    return CGPoint(x: c[0], y: h - c[1])      // -> CoreImage bottom-left origin
}
let srcURL = URL(fileURLWithPath: a[1]) as CFURL
guard let s = CGImageSourceCreateWithURL(srcURL, nil),
      let cg = CGImageSourceCreateImageAtIndex(s, 0, nil) else { exit(1) }
let H = CGFloat(cg.height)
let ci = CIImage(cgImage: cg)
let W_out = Int(a[3])!, H_out = Int(a[4])!

let fil = CIFilter(name: "CIPerspectiveCorrection")!
fil.setValue(ci, forKey: kCIInputImageKey)
fil.setValue(CIVector(cgPoint: pt(a[5], H)), forKey: "inputTopLeft")
fil.setValue(CIVector(cgPoint: pt(a[6], H)), forKey: "inputTopRight")
fil.setValue(CIVector(cgPoint: pt(a[7], H)), forKey: "inputBottomRight")
fil.setValue(CIVector(cgPoint: pt(a[8], H)), forKey: "inputBottomLeft")
guard var out = fil.outputImage else { exit(2) }
out = out.transformed(by: CGAffineTransform(translationX: -out.extent.origin.x,
                                            y: -out.extent.origin.y))
// non-uniform scale onto the target card, then a gentle sharpen to pay back
// what the upscale costs
let sx = CGFloat(W_out) / out.extent.width
let sy = CGFloat(H_out) / out.extent.height
out = out.transformed(by: CGAffineTransform(scaleX: sx, y: sy))
if let sh = CIFilter(name: "CISharpenLuminance") {
    sh.setValue(out, forKey: kCIInputImageKey)
    sh.setValue(0.55, forKey: "inputSharpness")
    out = sh.outputImage ?? out
}
let ctx = CIContext(options: [.outputColorSpace: CGColorSpaceCreateDeviceRGB()])
let rect = CGRect(x: 0, y: 0, width: W_out, height: H_out)
guard let img = ctx.createCGImage(out, from: rect) else { exit(3) }
let dst = URL(fileURLWithPath: a[2]) as CFURL
if let d = CGImageDestinationCreateWithURL(dst, UTType.png.identifier as CFString, 1, nil) {
    CGImageDestinationAddImage(d, img, nil); CGImageDestinationFinalize(d)
}
print("wrote \(a[2])  \(W_out)x\(H_out)  from quad \(Int(out.extent.width))x\(Int(out.extent.height))")
