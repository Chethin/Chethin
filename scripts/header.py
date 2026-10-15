"""Render the profile header card and link pills as SVGs (run once, output is committed).

    python3 scripts/header.py
"""
import base64
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ASSETS = os.path.join(ROOT, 'assets')
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'

ROLE = ('Forward Deployed Engineer', 'Lyra')
SUB = 'Co-founder of PaperSetter  ·  First-Class Honours @ ANU'
TAGLINE = 'I make software fast, and sometimes 3D.'


GREENS = ('#0e4429', '#006d32', '#26a641', '#39d353', '#7ee787')  # GitHub's contribution greens and a highlight
TONES = 8  # dot sizes


def face(cx, cy, height):
    """My face as a halftone (assets/face.json, from face.py), fading out at the neck."""
    f = json.load(open(os.path.join(ASSETS, 'face.json')))
    s = height / f['h']
    x0, y0 = cx - f['w'] * s / 2, cy - height / 2
    tones = [[] for _ in range(TONES)]
    for x, y, b in f['points']:
        tones[min(int(b * TONES), TONES - 1)].append(f'M{x0 + x * s:.1f} {y0 + y * s:.1f}h0')

    o = ['<defs><linearGradient id="neckfade" x1="0" y1="0" x2="0" y2="1"><stop offset=".86" stop-color="#fff"/>'
         '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>'
         f'<mask id="neck" maskUnits="userSpaceOnUse"><rect x="{x0:.1f}" y="{y0:.1f}" width="{f["w"] * s:.1f}" height="{height}" fill="url(#neckfade)"/></mask></defs>'
         '<g mask="url(#neck)" fill="none" stroke-linecap="round">']
    # brighter dots are bigger (area follows brightness) and climb through the contribution greens
    for t, d in enumerate(tones):
        o.append(f'<path stroke="{GREENS[t * len(GREENS) // TONES]}" stroke-width="{s * .9 * ((t + .5) / TONES) ** .5:.2f}" d="{"".join(d)}"/>')
    o.append('</g>')
    return ''.join(o)


def header():
    w, h = 720, 196
    name = base64.b64encode(open(os.path.join(ASSETS, 'name.png'), 'rb').read()).decode()
    cw = 7.25  # monospace advance at 12px
    n = len(TAGLINE) + 2
    type_end, dur = .35, 14
    widths = ';'.join(f'{min(i, n) * cw:.1f}' for i in range(n + 1))
    times = ';'.join(f'{type_end * i / n:.3f}' for i in range(n + 1))

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">',
         '<style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}.pulse{animation:pulse 2.4s ease-in-out infinite}'
         '@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cursor{animation:blink 1s step-end infinite}</style>',
         '<defs><clipPath id="card"><rect width="720" height="196" rx="10"/></clipPath>'
         '<radialGradient id="glow" gradientUnits="userSpaceOnUse" cx="600" cy="98" r="110"><stop offset="0" stop-color="#26a641" stop-opacity=".14"/>'
         '<stop offset="1" stop-color="#26a641" stop-opacity="0"/></radialGradient>'
         f'<clipPath id="typed"><rect x="40" y="148" height="20" width="0"><animate attributeName="width" values="{widths};{n * cw:.1f};0" '
         f'keyTimes="{times};.94;1" calcMode="discrete" dur="{dur}s" repeatCount="indefinite"/></rect></clipPath></defs>',
         '<g clip-path="url(#card)">',
         '<rect width="100%" height="100%" fill="#0d1117"/>'
         '<rect width="100%" height="100%" fill="url(#glow)"/>']

    # name, then role with a live "current" dot, then the muted second line
    o.append(f'<image x="40" y="34" width="420" height="46.4" href="data:image/png;base64,{name}"/>')
    o.append('<circle cx="45" cy="108" r="4" fill="none" stroke="#39d353">'
             '<animate attributeName="r" values="4;10" dur="2.4s" repeatCount="indefinite"/>'
             '<animate attributeName="opacity" values=".6;0" dur="2.4s" repeatCount="indefinite"/></circle>'
             '<circle class="pulse" cx="45" cy="108" r="3.5" fill="#39d353"/>')
    o.append(f'<text x="58" y="113" fill="#e6edf3" font-family="{SANS}" font-size="16" font-weight="500">{ROLE[0]} '
             f'<tspan fill="#7d8590" font-weight="400">@</tspan> <tspan fill="#39d353" font-weight="600">{ROLE[1]}</tspan></text>')
    o.append(f'<text x="40" y="137" fill="#9198a1" font-family="{SANS}" font-size="13" xml:space="preserve">{SUB}</text>')

    # terminal-style tagline that types itself out
    o.append(f'<g clip-path="url(#typed)"><text x="40" y="162" fill="#7ee787" font-family="{MONO}" font-size="12" '
             f'textLength="{n * cw:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">'
             f'<tspan fill="#484f58">&gt; </tspan>{TAGLINE}</text></g>')
    o.append(f'<rect class="cursor" y="152" width="7" height="13" fill="#7ee787" opacity=".8">'
             f'<animate attributeName="x" values="{";".join(f"{40 + min(i, n) * cw:.1f}" for i in range(n + 1))};{40 + n * cw:.1f};40" '
             f'keyTimes="{times};.94;1" calcMode="discrete" dur="{dur}s" repeatCount="indefinite"/></rect>')

    o.append(face(cx=600, cy=98, height=176))

    o.append('</g></svg>')
    with open(os.path.join(ASSETS, 'header.svg'), 'w') as f:
        f.write(''.join(o))


ICONS = {
    'web': '<circle cx="12" cy="12" r="10"/><path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"/><path d="M2 12h20"/>',
    'linkedin': '<path d="M16 8a6 6 0 0 1 6 6v7h-4v-7a2 2 0 0 0-2-2 2 2 0 0 0-2 2v7h-4v-7a6 6 0 0 1 6-6z"/><rect width="4" height="12" x="2" y="9"/><circle cx="4" cy="4" r="2"/>',
    'email': '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
}


def pill(key, label):
    cw = 7.8  # monospace advance at 13px
    w = round(14 + 16 + 9 + len(label) * cw + 16)
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 34" width="{w}" height="34">'
           f'<rect width="{w}" height="34" rx="17" fill="#161b22"/>'
           f'<g transform="translate(14 9) scale(.6667)" fill="none" stroke="#7ee787" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">{ICONS[key]}</g>'
           f'<text x="39" y="21.5" fill="#e6edf3" font-family="{MONO}" font-size="13" '
           f'textLength="{len(label) * cw:.1f}" lengthAdjust="spacingAndGlyphs">{label}</text></svg>')
    with open(os.path.join(ASSETS, f'link-{key}.svg'), 'w') as f:
        f.write(svg)


if __name__ == '__main__':
    header()
    for key, label in (('web', 'chethin.me'), ('linkedin', 'LinkedIn'), ('email', 'Email')):
        pill(key, label)
    print('wrote assets/header.svg and link pills')
