"""Render the profile header card and link pills as SVGs (run once, output is committed).

    python3 scripts/header.py
"""
import base64
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ASSETS = os.path.join(ROOT, 'assets')
SANS = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = 'ui-monospace,SFMono-Regular,Menlo,Consolas,monospace'
C = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']
EX, EY = (10.6, 4.0), (-9.0, 6.6)

ROLE = ('Forward Deployed Engineer', 'Lyra')
SUB = 'Co-founder of PaperSetter  ·  First-Class Honours @ ANU'
TAGLINE = 'I make software fast, and sometimes 3D.'


def mix(a, b, t):
    a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(p + (q - p) * t):02x}' for p, q in zip(a, b))


def tower(ox, oy, X, Y, h, l, lit):
    """A single isometric building in the city's style."""
    P = lambda x, y, z: (ox + x * EX[0] + y * EY[0], oy + x * EX[1] + y * EY[1] - z)
    pts = lambda ps: ' '.join(f'{x:.1f},{y:.1f}' for x, y in ps)
    x0, x1, y0, y1 = X + .12, X + .88, Y + .12, Y + .88
    out = [f'<polygon fill="{mix(C[l], "#000000", .48)}" points="{pts([P(x1, y0, 0), P(x1, y1, 0), P(x1, y1, h), P(x1, y0, h)])}"/>',
           f'<polygon fill="{mix(C[l], "#000000", .22)}" points="{pts([P(x0, y1, 0), P(x1, y1, 0), P(x1, y1, h), P(x0, y1, h)])}"/>',
           f'<polygon fill="{C[l]}" points="{pts([P(x0, y0, h), P(x1, y0, h), P(x1, y1, h), P(x0, y1, h)])}"/>']
    k = 0
    for z in range(4, int(h) - 3, 5):
        for u in (.1, .42):
            on = lit[k % len(lit)]
            k += 1
            fill = 'fill="#ffd866"' if on else 'fill="#c9d1d9" fill-opacity=".13"'
            out.append(f'<polygon {fill} points="{pts([P(x0 + u, y1, z), P(x0 + u + .24, y1, z), P(x0 + u + .24, y1, z + 2.4), P(x0 + u, y1, z + 2.4)])}"/>')
            out.append(f'<polygon {fill} points="{pts([P(x1, y0 + u, z), P(x1, y0 + u + .24, z), P(x1, y0 + u + .24, z + 2.4), P(x1, y0 + u, z + 2.4)])}"/>')
    return ''.join(out), P(X + .5, Y + .5, h)


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
         '@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}.cursor{animation:blink 1s step-end infinite}'
         '@keyframes ant{0%,60%{opacity:1}61%,100%{opacity:.15}}.ant{animation:ant 1.4s infinite}</style>',
         '<defs><clipPath id="card"><rect width="720" height="196" rx="10"/></clipPath>'
         '<radialGradient id="glow" cx=".86" cy=".75" r=".45"><stop offset="0" stop-color="#26a641" stop-opacity=".16"/>'
         '<stop offset="1" stop-color="#26a641" stop-opacity="0"/></radialGradient>'
         '<pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".8" fill="#e6edf3" fill-opacity=".06"/></pattern>'
         f'<clipPath id="typed"><rect x="40" y="148" height="20" width="0"><animate attributeName="width" values="{widths};{n * cw:.1f};0" '
         f'keyTimes="{times};.94;1" calcMode="discrete" dur="{dur}s" repeatCount="indefinite"/></rect></clipPath></defs>',
         '<g clip-path="url(#card)">',
         '<rect width="100%" height="100%" fill="#0d1117"/><rect width="100%" height="100%" fill="url(#dots)"/>'
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

    # a small cluster of buildings from the city, bottom right
    ox, oy = 590, 118
    s, cx, cy = 1.55, 612, 104  # scale the cluster up around its centre (598, 113)
    o.append(f'<g transform="matrix({s} 0 0 {s} {cx - s * 598:.2f} {cy - s * 113:.2f})">')
    o.append(f'<polygon fill="#0b0f14" stroke="#30363d" stroke-width=".8" points="'
             + ' '.join(f'{ox + x * EX[0] + y * EY[0]:.1f},{oy + x * EX[1] + y * EY[1]:.1f}' for x, y in ((-.3, -.3), (4.3, -.3), (4.3, 3.3), (-.3, 3.3))) + '"/>')
    spec = [(1, 0, 30, 3, [1, 0, 1, 1]), (3, 0, 18, 2, [0, 1]), (0, 1, 22, 2, [1, 1, 0]), (2, 1, 52, 4, [1, 0, 1, 1, 0, 1]),
            (3, 1, 12, 1, [0]), (0, 2, 9, 1, [0]), (1, 2, 38, 3, [0, 1, 1, 0, 1]), (3, 2, 26, 3, [1, 0]), (2, 2, 6, 1, [0])]
    for X, Y, hh, l, lit in sorted(spec, key=lambda s: (s[0] + s[1], s[0])):
        svg, top = tower(ox, oy, X, Y, hh, l, lit)
        o.append(svg)
        if hh == 52:
            o.append(f'<line x1="{top[0]:.1f}" y1="{top[1]:.1f}" x2="{top[0]:.1f}" y2="{top[1] - 9:.1f}" stroke="#8b949e" stroke-width=".8"/>'
                     f'<circle class="ant" cx="{top[0]:.1f}" cy="{top[1] - 9.5:.1f}" r="1.5" fill="#ff5c5c"/>')
    o.append('</g>')

    o.append('</g><rect x=".5" y=".5" width="719" height="195" rx="9.5" fill="none" stroke="#30363d"/></svg>')
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
           f'<rect x=".5" y=".5" width="{w - 1}" height="33" rx="16.5" fill="#0d1117" stroke="#30363d"/>'
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
