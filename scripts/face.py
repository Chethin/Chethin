"""Turn my GitHub avatar into a halftone of my face for the header (run once, output is committed).

    uv run --with numpy --with pillow python3 scripts/face.py

Writes assets/face.json (dot positions and brightness), which header.py draws.
"""
import json
import os
import urllib.request

import numpy as np
from PIL import Image, ImageFilter

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PHOTO = 'https://github.com/Chethin.png?size=460'
CROP = (100, 55, 352, 345)  # head and neck in the 460px avatar
PITCH = 4  # photo px between dots
WALL = .4  # grey this light or lighter is the wall, or the haze where my hair meets it; skin is never grey
SMOOTH = 6  # photo px of blur on my outline, so stray hairs and bumps melt away


def main():
    img = Image.open(urllib.request.urlopen(PHOTO)).convert('RGB').crop(CROP)
    l = np.asarray(img.convert('L'), dtype=float) / 255
    me = (l < WALL) | (np.asarray(img.convert('HSV'))[..., 1] >= 50)  # dark or skin-coloured
    outline = np.asarray(Image.fromarray(me.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(SMOOTH))) > 127
    dark, light = np.percentile(l[me], [2, 98])

    # hex grid of dots inside my outline, each as bright as the bits of me under it
    pts, dy = [], PITCH * 3 ** .5 / 2
    for j in range(int(l.shape[0] / dy)):
        for i in range(int(l.shape[1] / PITCH - .5)):
            x, y = (i + .5 + j % 2 / 2) * PITCH, (j + .5) * dy
            cell = np.s_[round(y - dy / 2):round(y + dy / 2), round(x - PITCH / 2):round(x + PITCH / 2)]
            if outline[cell].mean() < .5:
                continue
            m = me[cell]
            b = np.clip((l[cell][m].mean() - dark) / (light - dark), 0, 1) if m.any() else 0
            pts.append([round(x / PITCH, 1), round(y / PITCH, 1), round(b, 2)])

    with open(os.path.join(ROOT, 'assets', 'face.json'), 'w') as f:
        json.dump({'w': l.shape[1] / PITCH, 'h': l.shape[0] / PITCH, 'points': pts}, f, separators=(',', ':'))
    print(f'wrote assets/face.json: {len(pts)} dots')


if __name__ == '__main__':
    main()
