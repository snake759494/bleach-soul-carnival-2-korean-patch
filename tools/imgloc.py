"""Localise text-logo textures: detect text regions, redraw Korean in the original style, quantise to the palette."""
import sys, os, json, struct
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
import texdec
from swz import swizzle, unswizzle
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = os.path.join(ROOT, 'NanumSquareNeo-eHv.ttf')

def regions(im, colgap=None):
    """row bands by horizontal projection, then words by wide column gaps"""
    a = np.array(im)[:, :, 3] > 40
    h, w = a.shape
    rows = a.sum(1) > 0
    bands = []; y = 0
    while y < h:
        if rows[y]:
            y0 = y
            while y < h and rows[y]: y += 1
            bands.append((y0, y))
        else: y += 1
    # merge tiny bands (dakuten, small marks) into neighbours
    merged = []
    for b in bands:
        if merged and (b[1] - b[0] < 6 or b[0] - merged[-1][1] <= 1) and (b[1]-b[0] < 6 or merged[-1][1]-merged[-1][0] < 6):
            merged[-1] = (merged[-1][0], b[1])
        else: merged.append(b)
    out = []
    for y0, y1 in merged:
        cols = a[y0:y1].sum(0) > 0
        gap = colgap if colgap else max(8, (y1 - y0))
        segs = []; x = 0
        while x < w:
            if cols[x]:
                x0 = x; last = x
                while x < w and (cols[x] or x - last <= gap):
                    if cols[x]: last = x
                    x += 1
                segs.append((x0, last + 1))
            else: x += 1
        for x0, x1 in segs:
            sub = a[y0:y1, x0:x1]
            if sub.sum() < 12: continue
            ys = np.nonzero(sub.any(1))[0]
            out.append([x0, y0 + ys.min(), x1, y0 + ys.max() + 1])
    return out

def style(im, box):
    """fill colour per relative row, edge colour, inner ring colour"""
    x0, y0, x1, y1 = box
    arr = np.array(im.crop(box)).astype(int)
    a = arr[:, :, 3] > 200
    # distance from transparency (chebyshev, up to 4)
    dist = np.zeros(a.shape, int); cur = a.copy()
    for k in range(1, 6):
        er = cur.copy()
        er[1:, :] &= cur[:-1, :]; er[:-1, :] &= cur[1:, :]; er[:, 1:] &= cur[:, :-1]; er[:, :-1] &= cur[:, 1:]
        dist[cur & ~er] = k; cur = er
    dist[cur] = 6
    def med(mask):
        px = arr[mask]
        return tuple(int(v) for v in np.median(px, axis=0)) if len(px) else None
    edge = med(dist == 1); ring = med(dist == 2)
    rows = []
    H = a.shape[0]
    for y in range(H):
        sel = dist[y] >= 3
        c = med(np.vstack([np.zeros_like(dist[:y], bool), sel[None, :], np.zeros_like(dist[y + 1:], bool)])) if sel.any() else None
        rows.append(c)
    # fill gaps
    last = next((c for c in rows if c), (255, 255, 255, 255))
    for i in range(H):
        if rows[i] is None: rows[i] = last
        else: last = rows[i]
    return dict(edge=edge or (0, 0, 0, 255), ring=ring or edge or (0, 0, 0, 255), rows=rows)

def render_text(text, box, st, font=FONT):
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    lines = text.split('\n')
    # outline widths scale with height
    ow = max(1, round(H / 22))
    size = H
    best = None
    for s in range(max(6, int(H * 1.3)), 5, -1):
        f = ImageFont.truetype(font, s)
        bbs = [f.getbbox(l) for l in lines]
        lh = max(b[3] - b[1] for b in bbs); tw = max(b[2] - b[0] for b in bbs)
        th = lh * len(lines) + (len(lines) - 1) * max(1, s // 8)
        if th + 2 * ow <= H: best = (f, bbs, lh, tw, th, s); break
    f, bbs, lh, tw, th, s = best
    sx = min(1.0, (W - 2 * ow) / max(1, tw))
    canvas_w = int(tw) + 4 * ow + 4
    mask = Image.new('L', (canvas_w, H), 0); dr = ImageDraw.Draw(mask)
    y = (H - th) // 2
    for l, b in zip(lines, bbs):
        lw = b[2] - b[0]
        dr.text(((canvas_w - lw) // 2 - b[0], y - b[1]), l, font=f, fill=255)
        y += lh + max(1, s // 8)
    nw = max(1, int(canvas_w * sx)) if sx < 1 else canvas_w
    mask = mask.resize((nw, H), Image.LANCZOS)
    # compose layers on a W x H canvas, centred
    fillm = Image.new('L', (W, H), 0); fillm.paste(mask, ((W - nw) // 2, 0))
    ringm = fillm.filter(ImageFilter.MaxFilter(2 * ow + 1))
    edgem = ringm.filter(ImageFilter.MaxFilter(2 * max(1, ow // 2) + 1))
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(Image.new('RGBA', (W, H), st['edge']), (0, 0), edgem)
    out.paste(Image.new('RGBA', (W, H), st['ring']), (0, 0), ringm)
    grad = Image.new('RGBA', (W, H))
    rows = st['rows']
    grad.putdata([rows[min(len(rows) - 1, yy * len(rows) // H)] for yy in range(H) for _ in range(W)])
    out.paste(grad, (0, 0), fillm)
    return out

def quantise(img, pal):
    P = np.array(pal, int)                      # 256x4
    A = np.array(img).reshape(-1, 4).astype(int)
    # weight alpha strongly; fully transparent -> the palette's most transparent entry
    d = ((A[:, None, :3] - P[None, :, :3]) ** 2).sum(2) * (A[:, None, 3] / 255.0) + ((A[:, None, 3] - P[None, :, 3]) ** 2) * 2
    return d.argmin(1).astype(np.uint8)

def apply(d, key, texts):
    """patch texture in member bytes d (bytearray) in place; texts: list per region (None = keep)"""
    _, idx, p, ti = key.split('/'); p = int(p, 16); ti = int(ti)
    t = texdec.blocks_textures(d, p)[ti]
    im = texdec.decode(d, t)
    boxes = regions(im)
    if len(texts) == 1 and len(boxes) > 1 and texts[0] is not None and not isinstance(texts[0], list):
        pass
    assert len(boxes) == len(texts), (key, len(boxes), len(texts), boxes)
    new = im.copy()
    for box, tx in zip(boxes, texts):
        if tx is None: continue
        st = style(im, box)
        x0, y0, x1, y1 = box
        # clear the original ink (plus a little margin)
        clr = Image.new('RGBA', (x1 - x0 + 4, y1 - y0 + 4), (0, 0, 0, 0))
        new.paste(clr, (x0 - 2, y0 - 2))
        new.alpha_composite(render_text(tx, box, st), (x0, y0))
    st_ = t['stride']; h = t['h']; w = t['w']
    cl = d[t['clut']:t['clut'] + 1024]
    pal = [tuple(cl[4 * k:4 * k + 4]) for k in range(256)]
    full = Image.new('RGBA', (st_, h), (0, 0, 0, 0))
    # keep original pixels outside w
    orig_idx = unswizzle(bytes(d[t['pix']:t['pix'] + t['size']]), st_, h)
    full.paste(new, (0, 0))
    q = quantise(full, pal)
    q = q.reshape(h, st_)
    oi = np.frombuffer(orig_idx, np.uint8).reshape(h, st_)
    q[:, w:] = oi[:, w:]
    d[t['pix']:t['pix'] + t['size']] = swizzle(q.tobytes(), st_, h)
    return new

if __name__ == '__main__':
    from get import get
    keys = json.load(open(os.path.join(ROOT, 'work', 'ui_keys.json')))
    for k in sys.argv[1:]:
        key = keys[int(k)]
        _, n, i, p, ti = ['x'] + key.split('/')
        d = get('0006', int(key.split('/')[1]))
        t = texdec.blocks_textures(d, int(key.split('/')[2], 16))[int(key.split('/')[3])]
        im = texdec.decode(d, t)
        print(k, key, im.size, regions(im))
