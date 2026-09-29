"""Precise redraw of UI label text in the original style.

modes
  glow     white text, 1px navy edge, soft purple glow   (menu titles on transparent)
  outline  white text, 1px black outline                 (stat captions on transparent)
  plain    small dark text, no decoration                 (消費SP, 環, 空中 ...)
  plate    white text on a dark rounded plate; only the old glyph pixels are repainted
The old label is erased first (box + a small margin, never touching other boxes).
Text is drawn 4x supersampled and box-filtered down, optionally sheared for italics."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = {
    'heavy': os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf'),
    'xbold': os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf'),
    'bold': os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf'),
    'regular': os.path.join(ROOT, 'NanumSquareNeo-bRg.ttf'),
}
DEFAULT = {
    'glow': dict(font='heavy', ink=(255, 255, 255), edge=(40, 30, 120), glow=(130, 90, 210), deco=2, italic=0.0),
    'outline': dict(font='xbold', ink=(255, 255, 255), edge=(10, 10, 10), deco=2, italic=0.0),
    'plain': dict(font='regular', ink=(20, 20, 20), deco=0, italic=0.0),
    'plate': dict(font='xbold', ink=(255, 255, 255), deco=2, italic=0.0),
}
SS = 4


def text_mask(text, W, H, font, italic):
    """alpha mask (W x H floats 0..1) with the text fitted inside, supersampled"""
    lines = text.split('\n')
    n = len(lines)
    best = None
    for s in range(H * SS * 2, 4, -1):
        f = ImageFont.truetype(FONTS[font], s)
        bbs = [f.getbbox(l) for l in lines]
        lh = max(b[3] - b[1] for b in bbs)
        gap = s // 8
        th = lh * n + gap * (n - 1)
        if th <= H * SS:
            best = (f, bbs, lh, gap, th)
            break
    f, bbs, lh, gap, th = best
    tw = max(b[2] - b[0] for b in bbs)
    cw = tw + int(H * SS * italic) + 8
    im = Image.new('L', (cw, H * SS), 0)
    dr = ImageDraw.Draw(im)
    y = (H * SS - th) // 2
    for l, b in zip(lines, bbs):
        dr.text(((cw - (b[2] - b[0])) // 2 - b[0], y - b[1]), l, font=f, fill=255)
        y += lh + gap
    if italic:
        im = im.transform(im.size, Image.AFFINE, (1, italic, -italic * H * SS / 2, 0, 1, 0), Image.BICUBIC)
    # crop to ink, fit width
    bb = im.getbbox() or (0, 0, 1, 1)
    im = im.crop((bb[0], 0, bb[2], H * SS))
    w = im.width
    if w > W * SS:
        im = im.resize((W * SS, H * SS), Image.LANCZOS)
    out = Image.new('L', (W * SS, H * SS), 0)
    out.paste(im, ((W * SS - im.width) // 2, 0))
    small = out.resize((W, H), Image.BOX)
    return np.asarray(small, np.float32) / 255.0


def dilate(m, r):
    if r <= 0:
        return m
    im = Image.fromarray((m * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.MaxFilter(2 * r + 1)), np.float32) / 255.0


def blur(m, r):
    im = Image.fromarray((m * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(r)), np.float32) / 255.0


def over(dst, color, alpha):
    """alpha-composite a solid colour with per-pixel alpha onto RGBA float array"""
    a = alpha[..., None]
    c = np.array(color, np.float32)
    da = dst[..., 3:4] / 255.0
    oa = a + da * (1 - a)
    rgb = np.where(oa > 0, (c * a + dst[..., :3] * da * (1 - a)) / np.maximum(oa, 1e-6), 0)
    dst[..., :3] = rgb
    dst[..., 3:4] = oa * 255


def erase(A, box, others, pad):
    x0, y0, x1, y1 = box
    H, W = A.shape[:2]
    m = np.zeros((H, W), bool)
    m[max(0, y0 - pad):min(H, y1 + pad), max(0, x0 - pad):min(W, x1 + pad)] = True
    for o in others:
        m[o[1]:o[3], o[0]:o[2]] = False
    A[m] = 0


def draw(im, box, text, mode, others=(), style=None):
    st = dict(DEFAULT[mode])
    st.update(style or {})
    A = np.array(im.convert('RGBA'), np.float32)
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    d = st['deco']
    if mode == 'plate':
        # sample the plate colours, erase, then draw a fresh rounded plate
        sub = A[y0:y1, x0:x1]
        op = sub[..., 3] > 128
        lum = sub[..., :3] @ np.array([0.299, 0.587, 0.114])
        dark = op & (lum < 110)
        fill = tuple(int(v) for v in np.median(sub[dark][:, :3], 0)) if dark.any() else (30, 30, 100)
        bord = np.concatenate([sub[0], sub[-1], sub[:, 0], sub[:, -1]])
        bord = bord[bord[:, 3] > 60]
        edgec = tuple(int(v) for v in np.median(bord[:, :3], 0)) if len(bord) else (120, 90, 200)
        erase(A, box, others, st.get('pad', 2))
        plate = Image.new('L', (W * SS, H * SS), 0)
        ImageDraw.Draw(plate).rounded_rectangle([0, 0, W * SS - 1, H * SS - 1], radius=H * SS // 3, fill=255)
        pm = np.asarray(plate.resize((W, H), Image.BOX), np.float32) / 255.0
        inner = np.asarray(plate.filter(ImageFilter.MinFilter(2 * SS + 1)).resize((W, H), Image.BOX), np.float32) / 255.0
        reg = A[y0:y1, x0:x1]
        over(reg, st.get('edge', edgec), pm)
        over(reg, st.get('fill', fill), inner)
        A[y0:y1, x0:x1] = reg
    else:
        erase(A, box, others, st.get('pad', 3))
    m = text_mask(text, W - 2 * d, H - 2 * d, st['font'], st['italic'])
    full = np.zeros((H, W), np.float32)
    full[d:H - d, d:W - d] = m
    reg = A[y0:y1, x0:x1]
    if mode == 'glow':
        over(reg, st['glow'], np.clip(blur(dilate(full, 1), 1.2) * 0.9, 0, 1))
        over(reg, st['edge'], dilate(full, 1))
    elif mode == 'outline':
        over(reg, st['edge'], dilate(full, 2))
    elif mode == 'plain':
        full = np.clip((full - 0.2) * 1.5, 0, 1)
    over(reg, st['ink'], full)
    A[y0:y1, x0:x1] = reg
    return Image.fromarray(np.clip(A, 0, 255).astype(np.uint8), 'RGBA')
