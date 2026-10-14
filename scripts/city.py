"""Render the GitHub contribution graph as an animated isometric city (SVG).

Usage:
    GITHUB_TOKEN=... python3 scripts/city.py --user Chethin --out dist/city.svg
    python3 scripts/city.py --user Chethin --html contributions.html --out city.svg   # offline

Data comes from the GraphQL API when GITHUB_TOKEN is set, otherwise from the
public contributions page. Standard library only.
"""
import argparse
import datetime as dt
import json
import math
import os
import random
import re
import urllib.request
from zoneinfo import ZoneInfo

CYCLE = 20
C = ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']
BG = '#0d1117'
EX, EY = (10.6, 4.0), (-9.0, 6.6)
OX, OY = 104, 78
LEVELS = {'NONE': 0, 'FIRST_QUARTILE': 1, 'SECOND_QUARTILE': 2, 'THIRD_QUARTILE': 3, 'FOURTH_QUARTILE': 4}


# ---------------------------------------------------------------- data

def fetch_graphql(user, token):
    query = '''query($login: String!) { user(login: $login) { contributionsCollection { contributionCalendar {
        totalContributions weeks { contributionDays { date weekday contributionCount contributionLevel } } } } } }'''
    req = urllib.request.Request('https://api.github.com/graphql',
                                 data=json.dumps({'query': query, 'variables': {'login': user}}).encode(),
                                 headers={'Authorization': f'bearer {token}', 'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as r:
        body = json.load(r)
    if 'errors' in body:
        raise SystemExit(f'GraphQL error: {body["errors"]}')
    cal = body['data']['user']['contributionsCollection']['contributionCalendar']
    cells = {}
    for x, week in enumerate(cal['weeks']):
        for d in week['contributionDays']:
            cells[(x, d['weekday'])] = (dt.date.fromisoformat(d['date']), d['contributionCount'], LEVELS[d['contributionLevel']])
    return cells, cal['totalContributions']


def parse_html(html):
    tips = {}
    for cid, text in re.findall(r'<tool-tip[^>]*for="(contribution-day-component-\d+-\d+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r'\s*(\d+|No) contribution', text)
        tips[cid] = 0 if not m or m.group(1) == 'No' else int(m.group(1))
    cells = {}
    for tag in re.findall(r'<td[^>]*class="ContributionCalendar-day"[^>]*>', html):
        attrs = dict(re.findall(r'([\w-]+)="([^"]*)"', tag))
        d, x = map(int, attrs['id'].rsplit('-', 2)[1:])
        cells[(x, d)] = (dt.date.fromisoformat(attrs['data-date']), tips.get(attrs['id'], 0), int(attrs['data-level']))
    return cells, sum(c[1] for c in cells.values())


def fetch_html(user):
    with urllib.request.urlopen(f'https://github.com/users/{user}/contributions', timeout=30) as r:
        return r.read().decode()


def stats(cells, total):
    days = sorted(cells.values())
    longest = run = 0
    for _, n, _ in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    # like GitHub, an empty today doesn't break the streak until the day is over
    tail = days[:-1] if days and days[-1][1] == 0 else days
    current = 0
    for _, n, _ in reversed(tail):
        if not n:
            break
        current += 1
    best_date, best, _ = max(days, key=lambda t: t[1])
    return {'total': total, 'current': current, 'longest': longest, 'best': best, 'best_date': best_date}


# ---------------------------------------------------------------- drawing helpers

def P(X, Y, Z=0):
    return (OX + X * EX[0] + Y * EY[0], OY + X * EX[1] + Y * EY[1] - Z)


def L(X, Y, Z=0):
    return (X * EX[0] + Y * EY[0], X * EX[1] + Y * EY[1] - Z)


def pts(p):
    return ' '.join(f'{x:.1f},{y:.1f}' for x, y in p)


def poly(points, cls='', fill=''):
    c = f' class="{cls}"' if cls else ''
    f = f' fill="{fill}"' if fill else ''
    return f'<polygon{c}{f} points="{pts(points)}"/>'


def box(p, x0, x1, y0, y1, z0, z1, top, side_y, side_x):
    """The three visible faces of an axis-aligned box. Colours are (class, fill) pairs."""
    fx = [p(x1, y0, z0), p(x1, y1, z0), p(x1, y1, z1), p(x1, y0, z1)]
    fy = [p(x0, y1, z0), p(x1, y1, z0), p(x1, y1, z1), p(x0, y1, z1)]
    ft = [p(x0, y0, z1), p(x1, y0, z1), p(x1, y1, z1), p(x0, y1, z1)]
    return poly(fx, *side_x) + poly(fy, *side_y) + poly(ft, *top)


def mix(a, b, t):
    a, b = [int(a[i:i + 2], 16) for i in (1, 3, 5)], [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#' + ''.join(f'{round(p + (q - p) * t):02x}' for p, q in zip(a, b))


def cycle(name, prop, day, night):
    """A CSS class that follows the day/night cycle."""
    return (f'@keyframes {name}{{0%,35%{{{prop}:{day}}}45%,85%{{{prop}:{night}}}95%,100%{{{prop}:{day}}}}}'
            f'.{name}{{{prop}:{day};animation:{name} {CYCLE}s infinite}}')


def css():
    out = []
    for l in range(5):
        for face, shade in (('t', 0), ('f', .22), ('s', .48)):
            day = mix(C[l], '#000000', shade)
            out.append(cycle(f'{face}{l}', 'fill', day, mix(day, '#0a0f2a', .55)))
    out += [cycle('night', 'opacity', '0', '1'), cycle('day', 'opacity', '1', '0'),
            cycle('glass', 'fill', '#9ecbff', '#3b4a63'),
            cycle('pt', 'fill', '#1d2b26', '#121c22'), cycle('pf', 'fill', '#16211d', '#0d151a'),
            cycle('ps', 'fill', '#111a17', '#0a1014'),
            cycle('tr', 'fill', '#2f7360', '#1a3d3c'), cycle('trh', 'fill', '#48977e', '#24524f')]
    out.append('.w,' + ','.join(f'.w{i}' for i in range(6)) + '{fill:#c9d1d9;fill-opacity:.13}')
    out.append('@keyframes win{0%,37%{fill:#c9d1d9;fill-opacity:.13}44%,86%{fill:#ffd866;fill-opacity:.95}93%,100%{fill:#c9d1d9;fill-opacity:.13}}')
    out += [f'.w{i}{{animation:win {CYCLE}s infinite;animation-delay:{i * .35:.2f}s}}' for i in range(6)]
    out.append('@keyframes blink{0%,60%{opacity:1}61%,100%{opacity:.15}}.blink{animation:blink 1.4s infinite}')
    out.append('@keyframes shoot{0%,58%{opacity:0;transform:translate(0,0)}60%{opacity:1}64%,100%{opacity:0;transform:translate(90px,22px)}}'
               f'.shoot{{animation:shoot {CYCLE}s infinite}}')
    out.append('@keyframes dusk{0%,30%{opacity:0}40%{opacity:.75}49%,84%{opacity:0}91%{opacity:.6}100%{opacity:0}}'
               f'.dusk{{opacity:0;animation:dusk {CYCLE}s infinite}}')
    out.append('@keyframes flick{0%,100%{transform:scale(1,1)}30%{transform:scale(.94,1.08)}60%{transform:scale(1.04,.95)}}'
               '.flame{transform-box:fill-box;transform-origin:50% 100%;animation:flick 1.6s ease-in-out infinite}')
    sans = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
    out.append(f'.hero{{fill:#e6edf3;font:600 44px {sans};letter-spacing:-1.5px}}'
               f'.sub{{fill:#7d8590;font:400 12px {sans}}}'
               f'.streak{{fill:#e6edf3;font:500 15px {sans}}}'
               f'.meta{{fill:#7d8590;font:400 11px {sans}}}'
               f'.stamp{{fill:#484f58;font-size:9.5px;letter-spacing:.4px}}')
    return '<style>' + ''.join(out) + '</style>'


DEFS = ('<defs><clipPath id="frame"><rect width="720" height="372" rx="10"/></clipPath>'
        '<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0d1117"/><stop offset="1" stop-color="#1a2a44"/></linearGradient>'
        '<linearGradient id="search" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#fff2c2" stop-opacity=".45"/><stop offset="1" stop-color="#fff2c2" stop-opacity="0"/></linearGradient>'
        '<radialGradient id="glow"><stop offset="0" stop-color="#ffd866" stop-opacity=".45"/><stop offset="1" stop-color="#ffd866" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="duskg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#f0883e" stop-opacity="0"/>'
        '<stop offset=".7" stop-color="#f0883e" stop-opacity=".22"/><stop offset="1" stop-color="#db6d28" stop-opacity=".35"/></linearGradient>'
        '<radialGradient id="sunglow"><stop offset=".45" stop-color="#ffb84d" stop-opacity=".35"/><stop offset="1" stop-color="#ffb84d" stop-opacity="0"/></radialGradient>'
        '<linearGradient id="fire" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stop-color="#f85149"/><stop offset=".55" stop-color="#f0883e"/><stop offset="1" stop-color="#ffd866"/></linearGradient>'
        '<radialGradient id="headlight"><stop offset="0" stop-color="#fff2c2" stop-opacity=".38"/><stop offset="1" stop-color="#fff2c2" stop-opacity="0"/></radialGradient>'
        '<radialGradient id="taillight"><stop offset="0" stop-color="#ff4d4d" stop-opacity=".35"/><stop offset="1" stop-color="#ff4d4d" stop-opacity="0"/></radialGradient></defs>')

FLAME = ('<path class="flame" fill="url(#fire)" d="M7,0 C8,4 13,6.5 13,12 A6.5,6.5 0 0 1 0,12 C0,8.5 2,6.5 3.4,4.6 C3.8,6.6 4.8,7.8 6,8 C5.4,5.2 5.6,2.6 7,0 Z"/>'
         '<path class="flame" fill="#ffe9a8" d="M6.6,9 C7.4,11 9.6,12 9.6,14.4 A3.1,3.1 0 0 1 3.4,14.4 C3.4,12.4 5,11.6 6.6,9 Z"/>')


def car(color, forward):
    """Isometric car in local coords, length along X. forward=+1 drives toward +X."""
    top, mid, dark = mix(color, '#ffffff', .25), color, mix(color, '#000000', .35)
    ang = math.degrees(math.atan2(EX[1], EX[0]))

    def ground(X, rx, ry, extra):
        cx, cy = L(X, .28)
        return f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx}" ry="{ry}" transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})" {extra}/>'

    out = [ground(.8, 11, 3.2, 'fill="#000" opacity=".45"'),
           ground(3.1 if forward > 0 else -1.5, 13, 4.5, 'class="night" fill="url(#headlight)"'),
           ground(-.3 if forward > 0 else 1.9, 5, 2.5, 'class="night" fill="url(#taillight)"'),
           box(L, 0, 1.6, 0, .56, 1.2, 4.6, ('', top), ('', mid), ('', dark))]
    for wx in (.32, 1.28):
        x, y = L(wx, .56, 1.5)
        out.append(f'<ellipse cx="{x:.1f}" cy="{y:.1f}" rx="1.9" ry="1.7" fill="#0b0d10"/><circle cx="{x:.1f}" cy="{y:.1f}" r=".7" fill="#8b949e"/>')
    cab0, cab1 = .45, 1.15
    out.append(box(L, cab0, cab1, .06, .5, 4.6, 7.8, ('', top), ('', mid), ('', dark)))
    for u0, u1 in ((cab0 + .06, cab0 + .32), (cab0 + .38, cab1 - .06)):
        out.append(poly([L(u0, .5, 5.1), L(u1, .5, 5.1), L(u1, .5, 7.3), L(u0, .5, 7.3)], 'glass'))
    out.append(poly([L(cab1, .12, 5.1), L(cab1, .44, 5.1), L(cab1, .44, 7.3), L(cab1, .12, 7.3)], 'glass'))
    front, back = ('#fff6c2', '#ff4d4d') if forward > 0 else ('#ff4d4d', '#fff6c2')
    for v0, v1 in ((.06, .18), (.38, .5)):
        out.append(poly([L(1.6, v0, 3), L(1.6, v1, 3), L(1.6, v1, 4.2), L(1.6, v0, 4.2)], '', front))
    out.append(poly([L(0, .5, 3), L(.12, .5, 3), L(.12, .5, 4.2), L(0, .5, 4.2)], '', back))
    return ''.join(out)


# ---------------------------------------------------------------- scene

def render(cells, total, tz):
    rng = random.Random(42)  # fixed seed so the skyline doesn't reshuffle every run
    W, H = max(x for x, _ in cells) + 1, 7
    st = stats(cells, total)
    rep = f'dur="{CYCLE}s" repeatCount="indefinite"'
    o = [css(), DEFS, '<g clip-path="url(#frame)">', f'<rect width="100%" height="100%" fill="{BG}"/>',
         '<rect class="day" width="100%" height="100%" fill="url(#sky)"/>',
         '<rect class="dusk" width="100%" height="100%" fill="url(#duskg)"/>']

    # sky; stars stay clear of the stats so the numbers read cleanly
    stars = 0
    while stars < 40:
        sx, sy = rng.uniform(0, 720), rng.uniform(5, 190)
        if sx > 420 and sy < 165:
            continue
        o.append(f'<circle class="night" cx="{sx:.0f}" cy="{sy:.0f}" r="{rng.choice((.6, .8, 1.1))}" fill="#fff"/>')
        stars += 1
    o.append('<g class="night"><line class="shoot" x1="150" y1="6" x2="170" y2="11" stroke="#fff" stroke-width="1.1" stroke-linecap="round"/></g>')
    for cy, dur, sc, off in ((20, 80, 1, 0), (44, 110, .7, -60)):
        o.append(f'<g class="day"><g><g transform="scale({sc})" fill="#e6edf3" opacity=".12">'
                 f'<ellipse cx="0" cy="{cy / sc}" rx="26" ry="7"/><ellipse cx="12" cy="{cy / sc - 6}" rx="14" ry="8"/><ellipse cx="-10" cy="{cy / sc - 3}" rx="10" ry="6"/></g>'
                 f'<animateTransform attributeName="transform" type="translate" from="-60 0" to="780 0" dur="{dur}s" begin="{off}s" repeatCount="indefinite"/></g></g>')
    # sun rises at dawn (88%) and sets at dusk (42%), sinking behind the skyline with a fade at both ends
    arc = 'M70,128 Q215,-40 360,160'
    o.append(f'<g><circle r="26" fill="url(#sunglow)"/><circle r="11" fill="#ffb84d"/>'
             f'<animateMotion path="{arc}" keyPoints=".22;1;1;0;.22" keyTimes="0;.42;.88;.8801;1" calcMode="linear" {rep}/>'
             f'<animate attributeName="opacity" values="1;1;0;0;1;1" keyTimes="0;.37;.42;.88;.93;1" {rep}/></g>')
    o.append(f'<g><circle r="9" fill="#e6edf3"/><circle cx="3" cy="2" r="2" fill="#c9d1d9"/><circle cx="-3" cy="-2" r="1.3" fill="#c9d1d9"/>'
             f'<animateMotion path="{arc}" keyPoints="0;0;1;1" keyTimes="0;.42;.9;1" calcMode="linear" {rep}/>'
             f'<animate attributeName="opacity" values="0;0;1;1;0;0" keyTimes="0;.42;.47;.85;.9;1" {rep}/></g>')

    # stats: one hero number, the streak as a supporting line, everything else muted
    tx = 486
    o.append(f'<text x="{tx}" y="62" class="hero">{st["total"]:,}</text>'
             f'<text x="{tx + 1}" y="82" class="sub">contributions in the last year</text>'
             f'<g transform="translate({tx + 1} 98)">{FLAME}</g>'
             f'<text x="{tx + 20}" y="115" class="streak"><tspan fill="#f0883e" font-weight="600">{st["current"]}</tspan> day streak</text>'
             f'<text x="{tx + 1}" y="138" class="meta">Longest {st["longest"]} days · Best day {st["best_date"]:%b %-d}</text>')

    # diorama slab with month labels on its front edge
    sx0, sx1, sy0, sy1, th = -.4, W + .4, -.4, 8.9, 12
    o.append(poly([P(sx1, sy0), P(sx1, sy1), P(sx1, sy1, -th), P(sx1, sy0, -th)], '', '#11161c'))
    o.append(poly([P(sx0, sy1), P(sx1, sy1), P(sx1, sy1, -th), P(sx0, sy1, -th)], '', '#1a2028'))
    o.append(poly([P(sx0, sy0), P(sx1, sy0), P(sx1, sy1), P(sx0, sy1)], '', '#0b0f14'))
    o.append(f'<polyline points="{pts([P(sx0, sy1), P(sx1, sy1), P(sx1, sy0)])}" fill="none" stroke="#30363d" stroke-width=".8"/>')
    n = math.hypot(*EX)
    last = None
    for x in range(W):
        first = min((cells[(x, d)][0] for d in range(H) if (x, d) in cells), default=None)
        if first and first.strftime('%b') != last and x < W - 2:
            lx, ly = P(x + .2, sy1, -8.5)
            o.append(f'<text transform="matrix({EX[0] / n:.3f} {EX[1] / n:.3f} 0 1 {lx:.1f} {ly:.1f})" fill="#6e7681" font-size="7" letter-spacing=".5">{first.strftime("%b").upper()}</text>')
            last = first.strftime('%b')

    # road along the front edge
    o.append(poly([P(sx0, 7.2), P(sx1, 7.2), P(sx1, 8.7), P(sx0, 8.7)], '', '#161b22'))
    o.append(poly([P(sx0, 7.05), P(sx1, 7.05), P(sx1, 7.2), P(sx0, 7.2)], '', '#2d333b'))
    a, b = P(sx0, 7.95), P(sx1, 7.95)
    o.append(f'<line x1="{a[0]:.1f}" y1="{a[1]:.1f}" x2="{b[0]:.1f}" y2="{b[1]:.1f}" stroke="#6e7681" stroke-width=".8" stroke-dasharray="6 7"/>')
    lamps = range(2, W, 7)
    for lx in lamps:
        cx, cy = P(lx + .5, 7.95)
        o.append(f'<ellipse class="night" cx="{cx:.1f}" cy="{cy:.1f}" rx="16" ry="7" fill="url(#glow)"/>')

    # buildings and parks, back to front
    g = .12
    best = max(cells, key=lambda c: (cells[c][1], cells[c][0]))
    peak = max(cells[best][1], 1)
    for x, y in sorted(cells, key=lambda c: (c[0] + c[1], c[0])):
        _, count, l = cells[(x, y)]
        x0, x1, y0, y1 = x + g, x + 1 - g, y + g, y + 1 - g
        if l == 0:
            o.append(box(P, x0, x1, y0, y1, 0, 1.2, ('pt', ''), ('pf', ''), ('ps', '')))
            if rng.random() < .45:
                cx, cy = P(x + .5, y + .5, 1.2)
                o.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{cx:.1f}" y2="{cy - 3.5:.1f}" stroke="#3b2f25" stroke-width="1"/>'
                         f'<circle class="tr" cx="{cx:.1f}" cy="{cy - 6:.1f}" r="3.4"/><circle class="trh" cx="{cx - 1:.1f}" cy="{cy - 7:.1f}" r="1.6"/>')
            continue
        h = 4 + 44 * math.sqrt(count / peak) + rng.uniform(-1, 1)
        o.append(box(P, x0, x1, y0, y1, 0, h, (f't{l}', ''), (f'f{l}', ''), (f's{l}', '')))
        if h >= 12:
            for z in range(4, int(h) - 3, 5):
                for u in (.1, .42):
                    for face in 'yx':
                        cls = 'w' if rng.random() < .3 else f'w{rng.randrange(6)}'
                        if face == 'y':
                            q = [P(x0 + u, y1, z), P(x0 + u + .24, y1, z), P(x0 + u + .24, y1, z + 2.4), P(x0 + u, y1, z + 2.4)]
                        else:
                            q = [P(x1, y0 + u, z), P(x1, y0 + u + .24, z), P(x1, y0 + u + .24, z + 2.4), P(x1, y0 + u, z + 2.4)]
                        o.append(poly(q, cls))
        rx, ry = P(x + .5, y + .5, h)
        if (x, y) == best:
            o.append(f'<polygon class="night" points="{rx:.1f},{ry:.1f} {rx - 16:.1f},{ry - 170:.1f} {rx + 16:.1f},{ry - 170:.1f}" fill="url(#search)">'
                     f'<animateTransform attributeName="transform" type="rotate" values="-28 {rx:.1f} {ry:.1f};28 {rx:.1f} {ry:.1f};-28 {rx:.1f} {ry:.1f}" dur="7s" repeatCount="indefinite"/></polygon>'
                     f'<ellipse cx="{rx:.1f}" cy="{ry:.1f}" rx="3" ry="1.4" fill="#e6edf3"/>')
        elif h > 34 and rng.random() < .45:
            o.append(f'<line x1="{rx:.1f}" y1="{ry:.1f}" x2="{rx:.1f}" y2="{ry - 8:.1f}" stroke="#8b949e" stroke-width=".7"/>'
                     f'<circle class="blink" cx="{rx:.1f}" cy="{ry - 8.5:.1f}" r="1.3" fill="#ff5c5c" style="animation-delay:{rng.uniform(0, 1.4):.2f}s"/>')

    # street lamps, then traffic; cars fade in and out at the ends of the slab
    for lx in lamps:
        bx, by = P(lx + .5, 7.12)
        o.append(f'<line x1="{bx:.1f}" y1="{by:.1f}" x2="{bx:.1f}" y2="{by - 15:.1f}" stroke="#484f58" stroke-width="1.1"/>'
                 f'<circle class="night" cx="{bx:.1f}" cy="{by - 15.5:.1f}" r="1.6" fill="#ffd866"/>'
                 f'<circle cx="{bx:.1f}" cy="{by - 15.5:.1f}" r="1.6" fill="none" stroke="#6e7681" stroke-width=".6"/>')
    for color, lane, fwd, dur, delay in (('#a5d6ff', 7.32, -1, 15, 0), ('#ff7b72', 8.02, 1, 11, 0), ('#e3b341', 8.02, 1, 11, -5.5)):
        a, b = P(sx0 + .1, lane), P(sx1 - 1.7, lane)
        if fwd < 0:
            a, b = b, a
        t = f'dur="{dur}s" begin="{delay}s" repeatCount="indefinite"'
        o.append(f'<g>{car(color, fwd)}<animateMotion path="M{a[0]:.1f},{a[1]:.1f} L{b[0]:.1f},{b[1]:.1f}" {t}/>'
                 f'<animate attributeName="opacity" values="0;1;1;0" keyTimes="0;.07;.93;1" {t}/></g>')

    now = dt.datetime.now(ZoneInfo(tz))
    o.append(f'<text x="24" y="356" class="stamp">Updated {now:%-d %b %Y}, {now:%-I:%M} {now:%p}'.replace('AM', 'am').replace('PM', 'pm')
             + f' {now:%Z}</text>')
    o.append('</g>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 372" width="720" height="372" '
            'font-family="ui-monospace,SFMono-Regular,Menlo,monospace">' + ''.join(o) + '</svg>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--user', required=True)
    ap.add_argument('--out', default='dist/city.svg')
    ap.add_argument('--html', help='read a saved contributions page instead of fetching')
    ap.add_argument('--tz', default=os.environ.get('CITY_TZ', 'Australia/Sydney'))
    args = ap.parse_args()

    token = os.environ.get('GITHUB_TOKEN')
    if args.html:
        cells, total = parse_html(open(args.html).read())
    elif token:
        cells, total = fetch_graphql(args.user, token)
    else:
        cells, total = parse_html(fetch_html(args.user))
    if not cells:
        raise SystemExit('no contribution data found')

    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w') as f:
        f.write(render(cells, total, args.tz))
    st = stats(cells, total)
    print(f'wrote {args.out}: {len(cells)} days, {total} contributions, streak {st["current"]}, longest {st["longest"]}')


if __name__ == '__main__':
    main()
