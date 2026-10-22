#!/usr/bin/env python3
"""Generates business-card.html.

The card artwork is the approved illustration itself, not a redraw: the
reference mockup photo was perspective-corrected to a flat 90x54mm card
(tools/rectify.swift), the old wordmark and contact block were erased by
inpainting the cream panel (tools/prep.swift), and the result lives in
tools/card-art/. This script lays the real Jeevo logo and the real contact
details back on top as live text, so the type stays sharp and editable while
the painted border, arches, fort, lotus band and compass are untouched.

    python3 tools/make_card.py        # rewrites business-card.html
"""
import base64, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ---------------------------------------------------------------- geometry
# The art plates are 1133x708px covering a 96x60mm page: a 90x54mm card with
# 3mm of bleed (35px) on every side. Card coordinates below are measured on
# the 1063x638 trim area, which is how the artwork was marked up.
PAGE_W, PAGE_H = 96.0, 60.0
ART_W,  ART_H  = 1133.0, 708.0
BLEED          = 35.0
PPMM           = ART_W / PAGE_W          # 11.80 px per mm

def x(px):  return (BLEED + px) / PPMM   # card-x  -> mm from the page's left
def y(px):  return (BLEED + px) / PPMM   # card-y  -> mm from the page's top
def d(px):  return px / PPMM             # a length in card px -> mm

def f(v):   return ('%.3f' % v).rstrip('0').rstrip('.')

# ------------------------------------------------------------------ colour
# All sampled off the original artwork so the new type sits in the same light.
INK   = '#4A0D08'     # headings and body
SUB   = '#8A4A1E'     # the FOUNDER line, city lines
RULE  = '#9A5A28'     # hairlines
GOLD  = '#A15000'     # the diamond on the divider
DISC  = '#54110C'     # icon discs

def b64(name):
    with open(os.path.join(HERE, 'card-art', name), 'rb') as fh:
        return 'data:image/jpeg;base64,' + base64.b64encode(fh.read()).decode()

# ------------------------------------------------------------------- icons
GLYPH = {
 'phone': '<path d="M6.1 3.6c.5-.5 1.4-.4 1.8.2l1.1 1.6c.3.5.2 1.2-.2 1.6l-.8.7c.6 1.4 1.7 2.5 3.1 3.1l.7-.8c.4-.4 1.1-.5 1.6-.2l1.6 1.1c.6.4.7 1.3.2 1.8l-.8.8c-.6.6-1.4.8-2.1.6C8.6 13 5 9.4 4.1 5.5c-.2-.8 0-1.6.6-2.1z" fill="#fff"/>',
 'mail':  '<rect x="3.4" y="5.2" width="13.2" height="9.6" rx="1" fill="none" stroke="#fff" stroke-width="1.7"/>'
          '<path d="M3.9 5.8l6.1 4.6 6.1-4.6" fill="none" stroke="#fff" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"/>',
 'insta': '<rect x="4.1" y="4.1" width="11.8" height="11.8" rx="3.7" fill="none" stroke="#fff" stroke-width="1.7"/>'
          '<circle cx="10" cy="10" r="3.1" fill="none" stroke="#fff" stroke-width="1.7"/>'
          '<circle cx="13.5" cy="6.5" r="1.05" fill="#fff"/>',
 'web':   '<circle cx="10" cy="10" r="6.4" fill="none" stroke="#fff" stroke-width="1.6"/>'
          '<ellipse cx="10" cy="10" rx="2.7" ry="6.4" fill="none" stroke="#fff" stroke-width="1.5"/>'
          '<path d="M3.7 8h12.6M3.7 12h12.6" stroke="#fff" stroke-width="1.5"/>',
}
def icon(kind):
    return ('<svg class="ic" viewBox="0 0 20 20"><circle cx="10" cy="10" r="10" fill="%s"/>%s</svg>'
            % (DISC, GLYPH[kind]))

# Contact rows, measured against the original layout: icon discs on the same
# left margin, first text line on the disc's centre line.
ROWS = [
    ('phone', '+91 88004 92691', 'Gurugram, India',     268),
    ('phone', '+61 493 574 631', 'Brisbane, Australia', 341),
    ('mail',  'jeevotoursandtravels@gmail.com', '',     414),
    ('web',   'jeevo.co.in',                    '',     462),
    ('insta', '@jeevotoursandtravels',           '',    510),
]

def rows_html():
    out = []
    for kind, main, sub, top in ROWS:
        s = '<span class="sub">%s</span>' % sub if sub else ''
        out.append('<div class="row" style="top:%smm">%s<div class="tx">'
                   '<span class="main">%s</span>%s</div></div>'
                   % (f(y(top)), icon(kind), main, s))
    return '\n    '.join(out)

HTML = u'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Jeevo Tours and Travels — business card</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;500;600&family=Mukta:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  /* 90x54mm trim + 3mm bleed = 96x60mm page. The art plate already carries
     the bleed, so it fills the page edge to edge. */
  @page { size: 96mm 60mm; margin: 0; }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { background: #231F1C; }
  .card { position: relative; width: 96mm; height: 60mm; overflow: hidden;
          page-break-after: always; break-after: page; }
  .card:last-child { page-break-after: auto; break-after: auto; }
  .art { position: absolute; inset: 0; width: 100%; height: 100%;
         display: block; object-fit: fill; }

  /* ---------------- front ---------------- */
  .f-logo  { position: absolute; left: 50%; transform: translateX(-50%);
             top: __LOGO_T__mm; width: __LOGO_W__mm; }
  .f-logo svg { width: 100%; height: auto; display: block; }
  .f-tag   { position: absolute; left: 50%; transform: translateX(-50%);
             top: __TAG_T__mm; font-family: 'Playfair Display', serif;
             font-weight: 400; font-size: 5.8pt; letter-spacing: .02em;
             color: __INK__; white-space: nowrap; }

  /* ---------------- back ---------------- */
  .b-name  { position: absolute; left: __NAME_L__mm; top: __NAME_T__mm;
             font-family: 'Playfair Display', serif; font-weight: 500;
             font-size: 14pt; line-height: 1; color: __INK__; letter-spacing: .015em; }
  .b-role  { position: absolute; left: __ROLE_L__mm; top: __ROLE_T__mm;
             font-family: 'Mukta', sans-serif; font-weight: 500; font-size: 5.6pt;
             line-height: 1; letter-spacing: .36em; text-indent: .36em; color: __SUB__; }
  .b-rule  { position: absolute; left: __RULE_L__mm; top: __RULE_T__mm;
             width: __RULE_W__mm; height: .22mm; background: __RULE__; opacity: .62; }
  .b-rule::after { content: ""; position: absolute; left: __DIA_L__mm; top: -.5mm;
             width: 1.2mm; height: 1.2mm; background: __GOLD__;
             transform: rotate(45deg); border-radius: .12mm; }

  .row  { position: absolute; left: __ROW_L__mm; display: flex;
          align-items: flex-start; gap: __ROW_G__mm; }
  .ic   { flex: none; width: __IC__mm; height: __IC__mm; display: block; }
  .tx   { display: flex; flex-direction: column; }
  .main { font-family: 'Mukta', sans-serif; font-weight: 500; font-size: 5.9pt;
          line-height: __IC__mm; color: __INK__; letter-spacing: .008em; }
  .sub  { font-family: 'Mukta', sans-serif; font-weight: 400; font-size: 5.2pt;
          line-height: 1.05; color: __SUB__; letter-spacing: .045em; margin-top: .2mm; }

  @media screen {
    body { display: flex; flex-direction: column; align-items: center;
           gap: 10mm; padding: 10mm; }
    .card { box-shadow: 0 12px 38px rgba(0,0,0,.55); }
  }
</style>
</head>
<body>

<div class="card front">
  <img class="art" src="__FRONT_ART__" alt="">
  <div class="f-logo">__LOGO__</div>
  <div class="f-tag">Experiential Tours with a Personal Touch</div>
</div>

<div class="card back">
  <img class="art" src="__BACK_ART__" alt="">
  <div class="b-name">Jazz S</div>
  <div class="b-role">FOUNDER</div>
  <div class="b-rule"></div>
  __ROWS__
</div>

</body>
</html>
'''

def build():
    logo = open(os.path.join(HERE, 'logo.svg')).read().strip()
    sub = {
        '__LOGO_T__':  f(y(188)),  '__LOGO_W__': f(d(370)),
        '__TAG_T__':   f(y(356)),
        '__NAME_L__':  f(x(138)),  '__NAME_T__': f(y(135)),
        '__ROLE_L__':  f(x(150)),  '__ROLE_T__': f(y(208)),
        '__RULE_L__':  f(x(95)),   '__RULE_T__': f(y(252)),
        '__RULE_W__':  f(d(385)),  '__DIA_L__':  f(d(168)),
        '__ROW_L__':   f(x(95)),   '__ROW_G__':  f(d(25)),  '__IC__': f(d(32)),
        '__INK__': INK, '__SUB__': SUB, '__RULE__': RULE, '__GOLD__': GOLD,
        '__LOGO__': logo, '__ROWS__': rows_html(),
        '__FRONT_ART__': b64('card-front-art.jpg'),
        '__BACK_ART__':  b64('card-back-art.jpg'),
    }
    html = HTML
    for k, v in sub.items():
        html = html.replace(k, v)
    out = os.path.join(ROOT, 'business-card.html')
    open(out, 'w').write(html)
    print('wrote %s (%.1f KB)' % (out, len(html)/1024.0))

if __name__ == '__main__':
    build()
