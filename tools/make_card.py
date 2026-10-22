#!/usr/bin/env python3
"""Generates business-card.html — the Mughal-arch Jeevo card.

Everything ornamental (border, cusped arches, fort illustration, lotus band,
compass rose) is computed SVG so it stays sharp at any print resolution.
All type is HTML on top, so the real webfonts render and the text stays
editable without touching path data.

    python3 tools/make_card.py        # rewrites business-card.html
"""
import math, os, textwrap

# ---------------------------------------------------------------- geometry
# 1 unit = 0.1mm. Trim 90x54mm, 3mm bleed all round -> 96x60mm page.
U   = 10
PW, PH = 960, 600                      # page incl. bleed
TX0, TY0, TX1, TY1 = 30, 30, 930, 570  # trim
B   = 20                               # maroon border inside the trim
IX0, IY0, IX1, IY1 = TX0+B, TY0+B, TX1-B, TY1-B   # 50,50,910,550
WIN = 180                              # arch window column width
LW0, LW1 = IX0, IX0+WIN                # 50..230
RW0, RW1 = IX1-WIN, IX1                # 730..910
CP0, CP1 = LW1+10, RW0-10              # centre panel 240..720

# ------------------------------------------------------------------ colour
MAROON   = '#6B1A22'
MAROON_D = '#4C1118'
MAROON_L = '#8A2A30'
CREAM    = '#F4E8D3'
CREAM_D  = '#E7D5B6'
GOLD     = '#C68A3E'
GOLD_L   = '#E0A95E'
INK      = '#5E1620'

def f(x):
    """Trim pointless decimals so the path data stays readable."""
    return ('%.2f' % x).rstrip('0').rstrip('.')

def pts(s):
    return ' '.join(s.split())

# ------------------------------------------------- cusped (multifoil) arch
def _bez(p0, p1, p2, p3, t):
    m = 1 - t
    return (m*m*m*p0[0] + 3*m*m*t*p1[0] + 3*m*t*t*p2[0] + t*t*t*p3[0],
            m*m*m*p0[1] + 3*m*m*t*p1[1] + 3*m*t*t*p2[1] + t*t*t*p3[1])

def arch_path(x0, x1, ytop, yspring, ybot, cusps=6, bulge=0.56):
    """A pointed Mughal arch whose curve is broken into `cusps` scallops.

    Up the left jamb, over the cusped arch to a sharp ogee point, down the
    right jamb, along the foot. The lobes bulge into the opening, which is
    what makes it read as a multifoil rather than a cloud.
    """
    w  = x1 - x0
    cx = (x0 + x1) / 2.0
    rise = yspring - ytop
    p0 = (x0, yspring)
    p1 = (x0, yspring - rise*0.52)
    p2 = (cx - w*0.34, ytop + rise*0.10)
    p3 = (cx, ytop)
    left  = [_bez(p0, p1, p2, p3, i/float(cusps)) for i in range(cusps+1)]
    right = [(2*cx - x, y) for (x, y) in reversed(left)]

    segs  = [(left[i-1], left[i], i == cusps) for i in range(1, cusps+1)]
    segs += [(right[i-1], right[i], False)   for i in range(1, cusps+1)]

    d = ['M%s,%s' % (f(x0), f(ybot)), 'L%s,%s' % (f(x0), f(yspring))]
    for (a_, b_, straight) in segs:
        if straight:                      # a clean run into the ogee point
            d.append('L%s,%s' % (f(b_[0]), f(b_[1])))
            continue
        r = math.hypot(b_[0]-a_[0], b_[1]-a_[1]) * bulge
        d.append('A%s,%s 0 0 0 %s,%s' % (f(r), f(r), f(b_[0]), f(b_[1])))
    d += ['L%s,%s' % (f(x1), f(ybot)), 'Z']
    return ' '.join(d)

# ------------------------------------------------------- corner vine motif
def vine(scale=1.0, flip=False):
    """Leafy corner tendril, drawn into an 86x56 box with the stem at origin."""
    leaf = 'M0,0 C3.5,-6 11,-8 15,-3.5 C10.5,1.5 3.5,3.5 0,0 Z'
    buds = ((6, 44, -62), (15, 29, -44), (28, 16, -26), (46, 7, -12), (64, 2, 2))
    g = ['<g transform="scale(%s,%s)" opacity=".92">'
         % (f(-scale if flip else scale), f(scale))]
    g.append('<path d="M2,54 C2,34 9,18 25,9 C42,-1 62,-3 84,2" fill="none" '
             'stroke="%s" stroke-width="2" stroke-linecap="round"/>' % GOLD)
    for (bx, by, rot) in buds:
        g.append('<g transform="translate(%d,%d) rotate(%d)"><path d="%s" fill="%s"/></g>'
                 % (bx, by, rot, leaf, GOLD))
        g.append('<g transform="translate(%d,%d) rotate(%d) scale(.84)"><path d="%s" '
                 'fill="%s" opacity=".75"/></g>' % (bx, by, rot+152, leaf, GOLD_L))
    g.append('<circle cx="84" cy="2" r="2.4" fill="%s"/>' % GOLD_L)
    g.append('</g>')
    return ''.join(g)

# ------------------------------------------------------ 4-point star / rule
def star(cx, cy, r=9, fill=GOLD):
    d = ('M%s,%s C%s,%s %s,%s %s,%s C%s,%s %s,%s %s,%s '
         'C%s,%s %s,%s %s,%s C%s,%s %s,%s %s,%s Z') % (
        f(cx), f(cy-r),   f(cx+r*0.18), f(cy-r*0.18), f(cx+r*0.18), f(cy-r*0.18), f(cx+r), f(cy),
        f(cx+r*0.18), f(cy+r*0.18), f(cx+r*0.18), f(cy+r*0.18), f(cx), f(cy+r),
        f(cx-r*0.18), f(cy+r*0.18), f(cx-r*0.18), f(cy+r*0.18), f(cx-r), f(cy),
        f(cx-r*0.18), f(cy-r*0.18), f(cx-r*0.18), f(cy-r*0.18), f(cx), f(cy-r))
    return ('<path d="%s" fill="%s"/>'
            '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" '
            'stroke-width="1" opacity=".75"/>') % (
        d, fill, f(cx), f(cy), f(r*0.42), fill)

def ruled_star(x0, x1, y, r=9, col=None):
    col = col or GOLD
    gap = r + 10
    cx = (x0 + x1) / 2.0
    return (
        '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.1" opacity=".8"/>'
        '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.1" opacity=".8"/>%s'
        % (f(x0), f(y), f(cx-gap), f(y), col,
           f(cx+gap), f(y), f(x1), f(y), col, star(cx, y, r, col)))

# --------------------------------------------------------- lotus petal band
def lotus_band(x0, x1, y, h=24, step=44):
    """Repeating lotus-petal arcade along the foot of the back."""
    out = ['<g fill="none" stroke="%s" stroke-width="1.3" stroke-linejoin="round" '
           'opacity=".92">' % GOLD]
    n = max(1, int(round((x1 - x0) / float(step))))
    step = (x1 - x0) / float(n)
    for k in range(n):
        m, b = x0 + step*(k + 0.5), y + h
        out.append('<path d="M%s,%s C%s,%s %s,%s %s,%s C%s,%s %s,%s %s,%s Z"/>' % (
            f(m), f(b), f(m-step*0.33), f(b-h*0.34), f(m-step*0.21), f(y), f(m), f(y-h*0.06),
            f(m+step*0.21), f(y), f(m+step*0.33), f(b-h*0.34), f(m), f(b)))
        out.append('<path d="M%s,%s C%s,%s %s,%s %s,%s" opacity=".6"/>' % (
            f(m), f(b-h*0.14), f(m-step*0.13), f(b-h*0.44), f(m-step*0.08), f(y+h*0.22),
            f(m), f(y+h*0.12)))
        out.append('<circle cx="%s" cy="%s" r="1.8" fill="%s" stroke="none" opacity=".85"/>'
                   % (f(x0 + step*k), f(b-h*0.10), GOLD_L))
    out.append('<circle cx="%s" cy="%s" r="1.8" fill="%s" stroke="none" opacity=".85"/>'
               % (f(x1), f(y + h*0.90), GOLD_L))
    out.append('<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="1.1" '
               'opacity=".8"/>' % (f(x0), f(y+h), f(x1), f(y+h), GOLD))
    out.append('</g>')
    return ''.join(out)

# ------------------------------------------------------------ compass rose
def compass(cx, cy, r=17):
    long_, short = r, r*0.44
    spokes = []
    for a in (0, 90, 180, 270):
        spokes.append('<path d="M%s,%s L%s,%s L%s,%s L%s,%s Z" transform="rotate(%d %s %s)" fill="%s"/>'
                      % (f(cx), f(cy-long_), f(cx+r*0.13), f(cy), f(cx), f(cy+r*0.13), f(cx-r*0.13), f(cy),
                         a, f(cx), f(cy), GOLD))
    for a in (45, 135, 225, 315):
        spokes.append('<path d="M%s,%s L%s,%s L%s,%s L%s,%s Z" transform="rotate(%d %s %s)" fill="%s" opacity=".7"/>'
                      % (f(cx), f(cy-short), f(cx+r*0.09), f(cy), f(cx), f(cy+r*0.09), f(cx-r*0.09), f(cy),
                         a, f(cx), f(cy), GOLD))
    return (''.join(spokes) +
            '<circle cx="%s" cy="%s" r="%s" fill="none" stroke="%s" stroke-width="1.1" opacity=".8"/>'
            '<circle cx="%s" cy="%s" r="%s" fill="%s"/>'
            % (f(cx), f(cy), f(r*0.52), GOLD, f(cx), f(cy), f(r*0.14), GOLD_L))

# ====================================================================== art
# The fort: Amber-Fort-ish ridge palace over water, drawn in flat layered
# silhouettes so it holds up at any size and prints without halftone mush.
FORT_VB = (200, 600)            # matches the arch window's 1:3 opening

def _trees(rows):
    out = []
    for (tx, ty, r, col, op) in rows:
        out.append('<path fill="%s" opacity="%s" d="M%s,%s c-%s,0 -%s,-%s -%s,-%s '
                   'c0,-%s %s,-%s %s,-%s c%s,0 %s,%s %s,%s c0,%s -%s,%s -%s,%s Z"/>' % (
            col, op, f(tx), f(ty), f(r*.52), f(r*.95), f(r*.26), f(r*.95), f(r*.58),
            f(r*.78), f(r*.95), f(r*.95), f(r*1.90), f(r*.58),
            f(r*.95), f(r*.95), f(r*.95), f(r*.95), f(r*.58),
            f(r*.26), f(r*.95), f(r*.26), f(r*1.90), f(r*.26)))
    return ''.join(out)

def fort():
    """Amber-Fort-ish ridge palace over water, in flat layered silhouettes so
    it holds up at any size and prints without halftone mush."""
    o = []
    a = o.append
    a('<rect x="0" y="0" width="200" height="600" fill="url(#jvSky)"/>')
    a('<circle cx="124" cy="196" r="62" fill="#FBE3B6" opacity=".20"/>')
    a('<circle cx="124" cy="196" r="41" fill="#FDF0D6" opacity=".95"/>')
    a('<g fill="none" stroke="#85503C" stroke-width="1.6" stroke-linecap="round" opacity=".5">'
      '<path d="M44,130 c5,-5 9,-5 14,0"/><path d="M58,122 c5,-5 9,-5 14,0"/>'
      '<path d="M150,160 c4,-4 7,-4 11,0"/></g>')

    # haze bands behind the ranges keep the distance soft
    a('<rect x="0" y="250" width="200" height="60" fill="#F6CFA0" opacity=".30"/>')
    a('<path fill="#9B88AB" opacity=".42" d="%s"/>' % pts("""
        M0,300 C14,286 24,272 38,276 C50,280 58,296 70,290
        C84,283 92,262 108,268 C122,273 128,292 142,288
        C156,284 166,268 180,274 C190,278 196,290 200,296
        L200,600 L0,600 Z"""))
    a('<path fill="#7B6A8E" opacity=".52" d="%s"/>' % pts("""
        M0,326 C18,312 32,300 48,306 C62,311 70,326 86,322
        C102,318 112,302 128,308 C142,313 150,328 166,324
        C180,320 190,310 200,316 L200,600 L0,600 Z"""))

    # the ridge the fort stands on
    a('<path fill="#8A5739" d="%s"/>' % pts("""
        M0,372 C26,360 54,352 82,357 C118,364 150,388 200,408
        L200,600 L0,600 Z"""))
    a('<path fill="#A3703F" opacity=".5" d="%s"/>' % pts("""
        M0,380 C24,369 48,363 70,368 C98,374 124,392 158,408
        C176,416 190,422 200,427 L200,600 L0,600 Z"""))

    # ---- the fort ---------------------------------------------------------
    a('<g>')
    # curtain wall running down the ridge to the right
    a('<path fill="#A85634" d="M118,360 L190,398 L190,420 L118,382 Z"/>')
    for i in range(9):
        a('<rect x="%s" y="%s" width="5" height="6" fill="#B0603C"/>'
          % (f(120 + i*8), f(355 + i*4.2)))
    # main curtain
    a('<rect x="20" y="318" width="100" height="50" fill="#B5603A"/>')
    a('<rect x="20" y="318" width="50" height="50" fill="#C87249"/>')
    for i in range(13):
        a('<rect x="%s" y="312" width="5" height="6" fill="#C87249"/>' % f(21 + i*7.7))
    for i in range(6):
        x = 28 + i*15
        a('<path d="M%s,362 L%s,340 a6,6 0 0 1 12,0 L%s,362 Z" fill="#7B3522" opacity=".72"/>'
          % (f(x), f(x), f(x+12)))
    # round bastions
    for bx in (14, 106):
        a('<path d="M%s,370 L%s,322 a11,11 0 0 1 22,0 L%s,370 Z" fill="#C06A42"/>'
          % (f(bx), f(bx), f(bx+22)))
        a('<path d="M%s,322 a11,11 0 0 1 22,0 Z" fill="#D07E52"/>' % f(bx))
        for i in range(3):
            a('<rect x="%s" y="312" width="5" height="7" fill="#C06A42"/>' % f(bx+3+i*7.4))
    # raised keep
    a('<rect x="52" y="282" width="44" height="34" fill="#C87249"/>')
    a('<rect x="52" y="282" width="22" height="34" fill="#D5855A"/>')
    for i in range(6):
        a('<rect x="%s" y="276" width="5" height="6" fill="#D5855A"/>' % f(53 + i*7.4))
    for i in range(3):
        x = 58 + i*13
        a('<path d="M%s,312 L%s,296 a4.5,4.5 0 0 1 9,0 L%s,312 Z" fill="#7B3522" opacity=".6"/>'
          % (f(x), f(x), f(x+9)))
    a('<path d="M56,278 L92,278 L92,273 L56,273 Z" fill="#B5603A"/>')
    # chhatri on top: posts, dome, finial
    for px_ in (58, 70.6, 83.2):
        a('<rect x="%s" y="250" width="3" height="24" fill="#C87249"/>' % f(px_))
    a('<rect x="88" y="250" width="3" height="24" fill="#C87249"/>')
    a('<path d="M54,252 L94,252 L94,247 L54,247 Z" fill="#D5855A"/>')
    a('<path d="M56,247 C56,228 65,219 74,219 C83,219 92,228 92,247 Z" fill="#DE9263"/>')
    a('<path d="M56,247 C56,232 63,222 74,219 C70,228 68,236 68,247 Z" fill="#E7A478" opacity=".8"/>')
    a('<path d="M74,219 L74,207" stroke="#C87249" stroke-width="2"/>')
    a('<circle cx="74" cy="205" r="2.6" fill="#E7A97C"/>')
    # a small secondary dome
    a('<path d="M100,318 C100,304 106,297 113,297 C120,297 126,304 126,318 Z" fill="#CE7A4C"/>')
    a('<path d="M113,297 L113,289" stroke="#C06A42" stroke-width="1.7"/>')
    a('</g>')

    # trees along the foot of the ridge
    a(_trees([(6,432,17,'#3C5A3A',1),(26,420,20,'#3C5A3A',1),(48,428,15,'#44633F',1),
              (66,414,22,'#3C5A3A',1),(88,424,17,'#44633F',1),(108,418,19,'#3C5A3A',1),
              (128,436,15,'#44633F',1),(148,444,18,'#3C5A3A',1),(170,452,15,'#44633F',1),
              (190,460,16,'#3C5A3A',1)]))
    a(_trees([(16,442,13,'#2C4830','.75'),(56,438,15,'#2C4830','.75'),
              (96,440,13,'#2C4830','.75'),(136,452,13,'#2C4830','.75'),
              (178,466,13,'#2C4830','.75')]))

    # water. Flat vector water reads best as horizontal streaks: a bright
    # vertical column needs soft edges we cannot get cheaply, and a hard one
    # looks like a door.
    a('<rect x="0" y="458" width="200" height="142" fill="url(#jvWater)"/>')
    a('<rect x="0" y="458" width="200" height="70" fill="url(#jvGlint)"/>')
    a('<path fill="none" stroke="#243A28" stroke-width="7" opacity=".85" '
      'd="M0,461 C42,467 94,475 146,484 C172,489 190,493 200,496"/>')
    a('<path fill="none" stroke="#3E5C3C" stroke-width="2.6" opacity=".7" '
      'd="M0,466 C42,472 94,480 146,489 C172,494 190,498 200,501"/>')
    for (wy, wx0, wx1, hh, op) in (
            (470, 86,162,3.2,.42), (478, 16, 96,2.2,.22), (487,104,170,3.0,.36),
            (495,  6, 76,2.0,.19), (504, 90,154,2.8,.31), (514, 22,102,2.2,.21),
            (523,100,178,2.8,.27), (533,  4, 84,2.0,.17), (543, 86,160,2.6,.25),
            (553, 26,110,2.0,.17), (563,102,182,2.4,.21), (574,  8, 90,2.0,.15),
            (584, 92,166,2.2,.19), (593, 30,114,2.0,.14)):
        a('<rect x="%s" y="%s" width="%s" height="%s" rx="%s" fill="#FBEBCB" opacity="%s"/>'
          % (f(wx0), f(wy), f(wx1-wx0), f(hh), f(hh/2.0), op))
    return ''.join(o)

# =================================================================== plates# =================================================================== plates
def rrect(x0, y0, x1, y1, r=10):
    return ('M%s,%s L%s,%s A%s,%s 0 0 1 %s,%s L%s,%s A%s,%s 0 0 1 %s,%s '
            'L%s,%s A%s,%s 0 0 1 %s,%s L%s,%s A%s,%s 0 0 1 %s,%s Z') % (
        f(x0+r), f(y0), f(x1-r), f(y0), f(r), f(r), f(x1), f(y0+r),
        f(x1), f(y1-r), f(r), f(r), f(x1-r), f(y1),
        f(x0+r), f(y1), f(r), f(r), f(x0), f(y1-r),
        f(x0), f(y0+r), f(r), f(r), f(x0+r), f(y0))

def back_panel_path(x0, y0, x1, y1, r=10, big=76, cusps=4):
    """Rounded panel whose top-left corner opens into a cusped sweep."""
    p0 = (x0, y0+big); p1 = (x0, y0+big*0.30)
    p2 = (x0+big*0.30, y0); p3 = (x0+big, y0)
    sweep = [_bez(p0, p1, p2, p3, i/float(cusps)) for i in range(cusps+1)]
    d = ['M%s,%s' % (f(x0), f(y0+big))]
    for i in range(1, len(sweep)):
        ax, ay = sweep[i-1]; bx, by = sweep[i]
        rr = math.hypot(bx-ax, by-ay) * 0.60
        d.append('A%s,%s 0 0 0 %s,%s' % (f(rr), f(rr), f(bx), f(by)))
    d += ['L%s,%s' % (f(x1-r), f(y0)),
          'A%s,%s 0 0 1 %s,%s' % (f(r), f(r), f(x1), f(y0+r)),
          'L%s,%s' % (f(x1), f(y1-r)),
          'A%s,%s 0 0 1 %s,%s' % (f(r), f(r), f(x1-r), f(y1)),
          'L%s,%s' % (f(x0+r), f(y1)),
          'A%s,%s 0 0 1 %s,%s' % (f(r), f(r), f(x0), f(y1-r)),
          'Z']
    return ' '.join(d)

def window_use(x0, x1, y0, y1, uid, extra=''):
    """Drop the fort into a window, scaled to fill and centred."""
    w, h = x1-x0, y1-y0
    s = max(w/float(FORT_VB[0]), h/float(FORT_VB[1]))
    tx = x0 + (w - FORT_VB[0]*s)/2.0
    ty = y0 + (h - FORT_VB[1]*s)/2.0
    return ('<g clip-path="url(#%s)"><g transform="translate(%s,%s) scale(%s)" %s>'
            '<use href="#jvFort"/></g></g>'
            % (uid, f(tx), f(ty), f(s), extra))

DEFS = '''
<linearGradient id="jvSky" x1=".12" y1="0" x2=".55" y2="1">
  <stop offset="0" stop-color="#2E3A5E"/><stop offset=".13" stop-color="#5E4568"/>
  <stop offset=".27" stop-color="#9A5A57"/><stop offset=".40" stop-color="#C9754B"/>
  <stop offset=".53" stop-color="#E49C5C"/><stop offset=".68" stop-color="#F2C089"/>
  <stop offset=".84" stop-color="#F8DCB2"/><stop offset="1" stop-color="#F0C190"/>
</linearGradient>
<linearGradient id="jvWater" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#B68C5E"/><stop offset=".38" stop-color="#876348"/>
  <stop offset="1" stop-color="#554134"/>
</linearGradient>
<linearGradient id="jvGlint" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0" stop-color="#F6D6A4" stop-opacity=".42"/>
  <stop offset=".55" stop-color="#EBC28C" stop-opacity=".16"/>
  <stop offset="1" stop-color="#E0B37C" stop-opacity="0"/>
</linearGradient>
<radialGradient id="jvGlow" cx=".18" cy="0" r="1.15">
  <stop offset="0" stop-color="#FFFFFF" stop-opacity=".16"/>
  <stop offset=".55" stop-color="#FFFFFF" stop-opacity=".04"/>
  <stop offset="1" stop-color="#000000" stop-opacity=".14"/>
</radialGradient>
<radialGradient id="jvPaper" cx=".30" cy=".10" r="1.1">
  <stop offset="0" stop-color="#FBF2E2"/><stop offset=".55" stop-color="#F2E5CE"/>
  <stop offset="1" stop-color="#E6D4B4"/>
</radialGradient>
<linearGradient id="jvFade" x1="0" y1="0" x2="1" y2="0">
  <stop offset=".62" stop-color="#F2E5CE" stop-opacity="1"/>
  <stop offset=".76" stop-color="#F2E5CE" stop-opacity=".60"/>
  <stop offset=".90" stop-color="#F2E5CE" stop-opacity=".34"/>
  <stop offset="1" stop-color="#F2E5CE" stop-opacity=".28"/>
</linearGradient>
<linearGradient id="jvRule" x1="0" y1="0" x2="1" y2="0">
  <stop offset="0" stop-color="#C68A3E" stop-opacity=".25"/>
  <stop offset=".5" stop-color="#D9A055" stop-opacity="1"/>
  <stop offset="1" stop-color="#C68A3E" stop-opacity=".25"/>
</linearGradient>
<g id="jvFort">%s</g>
''' % fort()

# ==================================================================== faces
ARCH_TOP, ARCH_SPRING = IY0+44, IY0+190
ARCH_BOT  = IY1-10
LA0, LA1  = LW0+14, LW1-14          # left arch hole
RA0, RA1  = RW0+14, RW1-14

def front_svg():
    la = arch_path(LA0, LA1, ARCH_TOP, ARCH_SPRING, ARCH_BOT)
    ra = arch_path(RA0, RA1, ARCH_TOP, ARCH_SPRING, ARCH_BOT)
    lai = arch_path(LA0+7, LA1-7, ARCH_TOP+8, ARCH_SPRING, ARCH_BOT-7)
    rai = arch_path(RA0+7, RA1-7, ARCH_TOP+8, ARCH_SPRING, ARCH_BOT-7)
    panel = rrect(CP0, IY0, CP1, IY1, 12)
    page  = 'M0,0 L%d,0 L%d,%d L0,%d Z' % (PW, PW, PH, PH)
    o = ['<svg class="art" viewBox="0 0 %d %d" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">' % (PW, PH)]
    a = o.append
    a('<clipPath id="jvClipL"><path d="%s"/></clipPath>' % la)
    a('<clipPath id="jvClipR"><path d="%s"/></clipPath>' % ra)
    a('<rect x="0" y="0" width="%d" height="%d" fill="url(#jvPaper)"/>' % (PW, PH))
    a(window_use(LA0, LA1, ARCH_TOP, ARCH_BOT, 'jvClipL'))
    a(window_use(RA0, RA1, ARCH_TOP, ARCH_BOT, 'jvClipR'))
    # one maroon plate, three holes
    a('<path fill-rule="evenodd" fill="%s" d="%s %s %s %s"/>' % (MAROON, page, panel, la, ra))
    a('<path fill-rule="evenodd" fill="url(#jvGlow)" opacity=".55" d="%s %s %s %s"/>'
      % (page, panel, la, ra))
    # gold arch frames + capitals + plinths
    a('<g fill="none" stroke="%s" stroke-linejoin="round">' % GOLD)
    a('<path d="%s" stroke-width="2.4"/><path d="%s" stroke-width="2.4"/>' % (la, ra))
    a('<path d="%s" stroke-width="1.1" opacity=".7"/><path d="%s" stroke-width="1.1" opacity=".7"/>' % (lai, rai))
    a('</g>')
    for (a0, a1) in ((LA0, LA1), (RA0, RA1)):
        a('<g fill="%s" opacity=".9">' % GOLD)
        for cx in (a0, a1-9):
            a('<rect x="%s" y="%s" width="9" height="3" rx="1.2"/>' % (f(cx-1), f(ARCH_SPRING-2)))
            a('<rect x="%s" y="%s" width="11" height="4" rx="1.4"/>' % (f(cx-2), f(ARCH_BOT-5)))
        a('</g>')
    # centre panel hairline
    a('<path d="%s" fill="none" stroke="%s" stroke-width="1.4" opacity=".55"/>' % (panel, GOLD))
    # leafy flourishes in the two top corners
    for (vx, flip) in ((TX0+8, False), (TX1-8, True)):
        a('<g transform="translate(%s,%s)">%s</g>' % (f(vx), f(TY0+8), vine(0.72, flip)))
    # the two ruled stars inside the centre panel
    a(ruled_star(CP0+26, CP1-26, IY0+58))
    a(ruled_star(CP0+26, CP1-26, IY1-54))
    a('</svg>')
    return ''.join(o)

BP0, BP1 = IY0, IY1-38          # back panel top/bottom
def back_svg():
    panel = back_panel_path(IX0, BP0, IX1, BP1, r=10, big=84)
    page  = 'M0,0 L%d,0 L%d,%d L0,%d Z' % (PW, PW, PH, PH)
    o = ['<svg class="art" viewBox="0 0 %d %d" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">' % (PW, PH)]
    a = o.append
    a('<clipPath id="jvClipB"><path d="%s"/></clipPath>' % panel)
    a('<rect x="0" y="0" width="%d" height="%d" fill="url(#jvPaper)"/>' % (PW, PH))
    # ghosted fort, bleeding off the right of the panel
    a('<g clip-path="url(#jvClipB)"><g opacity=".42">%s</g>'
      '<rect x="0" y="0" width="%d" height="%d" fill="url(#jvFade)"/></g>'
      % (window_use(560, IX1+34, BP0-12, BP1+12, 'jvClipB'), PW, PH))
    a('<path fill-rule="evenodd" fill="%s" d="%s %s"/>' % (MAROON, page, panel))
    a('<path fill-rule="evenodd" fill="url(#jvGlow)" opacity=".55" d="%s %s"/>' % (page, panel))
    a('<path d="%s" fill="none" stroke="%s" stroke-width="1.4" opacity=".6"/>' % (panel, GOLD))
    a(lotus_band(IX0+6, IX1-6, BP1+12, h=22, step=43))
    a(compass(IX1-46, BP0+42, 17))
    a(ruled_star(110, 566, 212, 8))
    a('</svg>')
    return ''.join(o)

# ====================================================================== doc
ICON = {
 'phone': '<path d="M5.6 3.2c.5-.5 1.3-.4 1.7.2l1 1.5c.3.5.2 1.1-.2 1.5l-.7.6c.5 1.3 1.5 2.3 2.8 2.9l.6-.7c.4-.4 1-.5 1.5-.2l1.5 1c.6.4.7 1.2.2 1.7l-.7.7c-.5.5-1.2.7-1.9.5C8.1 12.1 4.9 8.9 4.1 5.4c-.2-.7 0-1.4.5-1.9z"/>',
 'mail':  '<path d="M3.2 4.8h11.6v8.4H3.2z" fill="none" stroke="#fff" stroke-width="1.5"/><path d="M3.6 5.3l5.4 4 5.4-4" fill="none" stroke="#fff" stroke-width="1.5" stroke-linecap="round"/>',
 'web':   '<circle cx="9" cy="9" r="5.6" fill="none" stroke="#fff" stroke-width="1.4"/><ellipse cx="9" cy="9" rx="2.4" ry="5.6" fill="none" stroke="#fff" stroke-width="1.3"/><path d="M3.6 7.2h10.8M3.6 10.8h10.8" stroke="#fff" stroke-width="1.3"/>',
}
def icon(kind):
    body = ICON[kind]
    fill = ' fill="#fff"' if kind == 'phone' else ''
    return ('<svg class="ic" viewBox="0 0 18 18"><circle cx="9" cy="9" r="9" fill="%s"/>'
            '<g%s>%s</g></svg>' % (MAROON, fill, body))

def row(kind, main, sub=''):
    s = '<span class="sub">%s</span>' % sub if sub else ''
    return ('<div class="row">%s<div class="tx"><span class="main">%s</span>%s</div></div>'
            % (icon(kind), main, s))

HTML = u'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Jeevo Tours and Travels — business card</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,400;1,500&family=Mukta:wght@400;500;600&family=Playfair+Display&display=swap" rel="stylesheet">
<style>
  /* 90x54mm trim + 3mm bleed = 96x60mm page. Crop marks sit in the bleed. */
  @page {{ size: 96mm 60mm; margin: 0; }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  html,body{{background:#2A2622}}
  .card{{position:relative;width:96mm;height:60mm;overflow:hidden;
    page-break-after:always;break-after:page;background:{MAROON}}}
  .card:last-child{{page-break-after:auto;break-after:auto}}
  .art{{position:absolute;inset:0;width:100%;height:100%;display:block}}
  .defs{{position:absolute;width:0;height:0;overflow:hidden}}

  /* ---- front ---- */
  .f-logo{{position:absolute;left:50%;transform:translateX(-50%);top:15.4mm;width:27mm}}
  .f-logo svg{{width:100%;height:auto;display:block}}
  .f-tours{{position:absolute;left:50%;transform:translateX(-50%);top:30.6mm;
    display:flex;align-items:center;gap:3.1mm;
    font-family:'Cormorant Garamond',serif;font-weight:600;font-size:8.4pt;
    letter-spacing:.44em;text-indent:.44em;color:{INK};white-space:nowrap}}
  .f-tours::before,.f-tours::after{{content:"";width:7.4mm;height:.28mm;
    background:{GOLD};opacity:.85}}
  .f-tag{{position:absolute;left:50%;transform:translateX(-50%);top:37.4mm;
    font-family:'Cormorant Garamond',serif;font-style:italic;font-weight:400;
    font-size:7.6pt;letter-spacing:.035em;color:{INK};opacity:.9;white-space:nowrap}}

  /* ---- back ---- */
  .b-name{{position:absolute;left:11mm;top:9.6mm;
    font-family:'Cormorant Garamond',serif;font-weight:600;font-size:15pt;
    line-height:1;color:{INK};letter-spacing:.02em}}
  .b-role{{position:absolute;left:11.3mm;top:16.6mm;
    font-family:'Mukta',sans-serif;font-weight:600;font-size:5.6pt;
    letter-spacing:.42em;text-indent:.42em;color:#8A5A2A}}
  .b-rows{{position:absolute;left:11mm;top:23.3mm;width:50mm}}
  .row{{display:flex;align-items:flex-start;gap:2.6mm;margin-bottom:2.5mm}}
  .row:last-child{{margin-bottom:0}}
  .ic{{flex:none;width:3.4mm;height:3.4mm;margin-top:.15mm;display:block}}
  .tx{{display:flex;flex-direction:column;gap:.5mm}}
  .main{{font-family:'Mukta',sans-serif;font-weight:500;font-size:6.6pt;
    line-height:1.12;color:{INK};letter-spacing:.012em}}
  .sub{{font-family:'Mukta',sans-serif;font-weight:400;font-size:5.6pt;
    line-height:1.12;color:#8A5A2A;letter-spacing:.07em}}

  /* ---- crop marks, in the bleed ---- */
  .crop i{{position:absolute;background:#111}}
  @media screen{{
    body{{display:flex;flex-direction:column;align-items:center;gap:10mm;padding:10mm}}
    .card{{box-shadow:0 10px 34px rgba(0,0,0,.5)}}
  }}
</style>
</head>
<body>
<svg class="defs" xmlns="http://www.w3.org/2000/svg"><defs>{DEFS}</defs></svg>

<div class="card front">
  {FRONT}
  <div class="f-logo">{LOGO}</div>
  <div class="f-tours">TOURS</div>
  <div class="f-tag">Experiential tours with a personal touch</div>
</div>

<div class="card back">
  {BACK}
  <div class="b-name">Jazz S</div>
  <div class="b-role">FOUNDER</div>
  <div class="b-rows">
    {ROWS}
  </div>
</div>
</body>
</html>
'''

def build():
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    logo = open(os.path.join(here, 'logo.svg')).read().strip()
    rows = '\n    '.join([
        row('phone', '+61 493 574 631', 'Brisbane, Australia'),
        row('phone', '+91 88004 92691', 'Gurugram, India'),
        row('mail',  'jeevotoursandtravels@gmail.com'),
        row('web',   'jeevo.co.in'),
    ])
    html = (HTML
        .replace('{MAROON}', MAROON).replace('{GOLD}', GOLD).replace('{INK}', INK)
        .replace('{DEFS}', DEFS).replace('{FRONT}', front_svg()).replace('{BACK}', back_svg())
        .replace('{LOGO}', logo).replace('{ROWS}', rows))
    # the CSS braces are doubled in the template so they survive the pass above
    html = html.replace('{{', '{').replace('}}', '}')
    out = os.path.join(root, 'business-card.html')
    open(out, 'w').write(html)
    print('wrote %s (%d bytes)' % (out, len(html)))

if __name__ == '__main__':
    build()
