"""Full build: python tools/build.py [out.iso]
1. load translations (translation/out/*.json) keyed by unique id
2. assign glyph indices to every non-ASCII char used, render Korean font into dig 0002 (GIM + width table)
3. re-encode every message table (work/blocks.json) and repack its string pool in place
4. apply fixed-length in-place strings (translation/inplace.json)
5. rebuild cfc.dig (recompress changed entries) and the ISO
"""
import sys, os, json, glob, re, struct
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from member import members
from kfont import build as build_font
from digbuild import build_dig, build_iso
from badge import patch as patch_badges
from gimpatch import patch as patch_gim

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SRC_ISO = 'Bleach - Soul Carnival 2 (Japan).iso'
TOK = re.compile(r'\{([0-9A-F]{4})\}')


def load_translations():
    U = json.load(open('work/uniq_codes.json'))
    tr = {}
    for p in sorted(glob.glob('translation/out/b*.json')):
        for k, v in json.load(open(p, encoding='utf8')).items():
            tr[int(k)] = v
    return U, tr


def glyph_set(texts):
    chars = set()
    for t in texts:
        for ch in TOK.sub('', t).replace('\n', ''):
            if not (0x20 <= ord(ch) < 0x7f) or ch == ',':
                chars.add(ch)
    # Hangul in code order after symbols, so the table is stable
    return sorted(chars, key=lambda c: (('가' <= c <= '힣'), c))


ASCII_FIX = {'.': 0x0C, '-': 0x0D, '_': 0x0E}  # font order: * + . - _ / ; there is no ',' glyph


def asc(ch):
    if ch in ASCII_FIX:
        return ASCII_FIX[ch]
    o = ord(ch)
    return o - 0x20 if o <= 0x5e else o - 0x21


def encode(t, cmap):
    out = []
    pos = 0
    t = t.replace('\n', '{8010}')
    for m in TOK.finditer(t):
        for ch in t[pos:m.start()]:
            out.append(asc(ch) if 0x20 <= ord(ch) < 0x7f and ch != ',' else cmap[ch])
        out.append(int(m.group(1), 16))
        pos = m.end()
    for ch in t[pos:]:
        out.append(asc(ch) if 0x20 <= ord(ch) < 0x7f and ch != ',' else cmap[ch])
    return out


def pack_codes(seq):
    return struct.pack('<%dH' % (len(seq) + 1), *(seq + [0x8000]))


def repack_block(d, b, new_strs, ext):
    """rewrite the string pool of table b in bytearray d.
    Strings that do not fit in the original pool go to ext (bytearray appended after the entry's data;
    ext['base'] is its file offset). The entry is loaded whole, so table offsets may point past the old end."""
    base = b['base']
    to = base if b['kind'] == 'A' else base + 4
    starts = [base + o for o in b['offs']]
    pool_start = min(starts)
    pool_end = b['end']
    cap = pool_end - pool_start
    if os.environ.get('EXT_ALL') == str(b.get('file')):
        cap = 0  # debug: force every string into the extension area
    blob = bytearray()
    where = {}
    offs = []
    for s in new_strs:
        key = tuple(s)
        if key not in where:
            raw = pack_codes(s)
            if len(blob) + len(raw) <= cap:
                where[key] = pool_start + len(blob)
                blob += raw
            else:
                where[key] = ext['base'] + len(ext['data'])
                ext['data'] += raw
        offs.append(where[key] - base)
    blob += bytes([0, 0x80]) * ((pool_end - pool_start - len(blob)) // 2)
    d[pool_start:pool_end] = blob
    struct.pack_into('<%dI' % len(offs), d, to, *offs)


def patch_sfo_title(iso_path, title):
    import pycdlib
    iso = pycdlib.PyCdlib(); iso.open(SRC_ISO)
    rec = iso.get_record(iso_path='/PSP_GAME/PARAM.SFO'); lba = rec.extent_location(); iso.close()
    f = open(iso_path, 'r+b'); f.seek(lba * 2048); d = bytearray(f.read(2048))
    kt, dt, n = struct.unpack_from('<III', d, 8)
    for i in range(n):
        ko, fmt, ln, mx, do = struct.unpack_from('<HHIII', d, 20 + 16 * i)
        k = d[kt + ko:d.index(0, kt + ko)].decode()
        if k == 'TITLE':
            v = title.encode('utf8') + bytes(1)
            assert len(v) <= mx
            d[dt + do:dt + do + mx] = v + bytes(mx - len(v))
            struct.pack_into('<I', d, 20 + 16 * i + 4, len(v))
    f.seek(lba * 2048); f.write(d); f.close()


def main(out_iso):
    U, tr = load_translations()
    missing = [i for i in range(len(U)) if i not in tr]
    if missing:
        print('번역 누락', len(missing), '개 — 원문 유지')
    inplace = json.load(open('translation/inplace.json', encoding='utf8')) if os.path.exists('translation/inplace.json') else []
    texts = list(tr.values()) + [x['ko'] for x in inplace]
    chars = glyph_set(texts)
    print('글리프', len(chars), '개 사용')

    # original glyph images to reuse for symbols
    ocr = json.load(open('work/ocr_raw.json', encoding='utf8'))
    fixes = json.load(open('translation/ocr_fix.json', encoding='utf8'))
    otab = [x[1] for x in ocr]
    for k, v in fixes.items():
        otab[int(k, 16)] = v
    reuse = {}
    for i, c in enumerate(otab[:0x712]):
        if i >= 0x5e and c in chars and not ('가' <= c <= '힣') and c not in reuse and ocr[i][0] > 0.8:
            reuse[c] = i
    cmap = {c: 0x5e + k for k, c in enumerate(chars)}

    # codes of every unique string (untranslated ones keep original codes: they would render garbage,
    # so the build refuses unless ALLOW_MISSING is set)
    if missing and not os.environ.get('ALLOW_MISSING'):
        raise SystemExit('번역이 모두 끝나야 빌드할 수 있습니다')
    newU = {}
    for i in range(len(U)):
        newU[tuple(U[i])] = encode(tr[i], cmap) if i in tr else [0x1f, 0x1f]

    B = json.load(open('work/blocks.json'))
    byfile = {}
    for b in B:
        byfile.setdefault(b['file'], []).append(b)
    for x in inplace:
        byfile.setdefault(x['file'], [])

    replaced = {}
    over = []
    ext_files = []
    for f, blocks in sorted(byfile.items()):
        d = bytearray(open('work/dig/%04d.bin' % f, 'rb').read())
        ext = {'base': (len(d) + 15) & ~15, 'data': bytearray()}
        for b in blocks:
            ns = [newU[tuple(s)] for s in b['strs']]
            repack_block(d, b, ns, ext)
        if ext['data']:
            d += bytes(ext['base'] - len(d)) + ext['data']
            d += bytes((-len(d)) % 16)
            ext_files.append((f, len(ext['data'])))
            if not os.environ.get('ALLOW_EXT'):
                over.append((f, 'ext', len(ext['data'])))
        for x in inplace:
            if x['file'] != f:
                continue
            seq = encode(x['ko'], cmap)
            room = x['len']  # u16 slots incl. terminator
            if len(seq) + 1 > room:
                over.append((f, x['off'], 'inplace'))
                continue
            d[x['off']:x['off'] + 2 * room] = pack_codes(seq) + b'\x00\x80' * (room - len(seq) - 1)
        replaced[f] = d
    print('풀 확장 파일', len(ext_files), '개, 총', sum(x[1] for x in ext_files), '바이트')
    if over:
        print('풀 초과:', over)
        json.dump(over, open('work/overflow.json', 'w'))
        raise SystemExit(1)

    # font into 0002
    d = replaced.setdefault(2, bytearray(open('work/dig/0002.bin', 'rb').read()))
    M = members(d)
    go = M[2]['off']
    g, widths = build_font(bytes(d[go:go + M[2]['size']]), chars, reuse)
    d[go:go + M[2]['size']] = g
    io = M[3]['off']
    d[io:io + M[3]['size']] = patch_badges(bytes(d[io:io + M[3]['size']]))
    wo = M[4]['off']
    for i, w in widths.items():
        d[wo + i] = w
    for i in range(0x5e + len(chars), 0x712):
        d[wo + i] = 0

    # images: apply each spec to every copy of the same page (same pixel hash) in any entry
    if os.path.exists('translation/images.json'):
        gidx = json.load(open('work/gim_index.json'))
        byhash = {}
        for x in gidx:
            byhash.setdefault(x['hash'], []).append(x)
        spec = []
        for p in sorted(glob.glob('translation/images_part*.json')):
            spec += json.load(open(p, encoding='utf8'))
        near = json.load(open('work/neardup.json')) if os.path.exists('work/neardup.json') else {}
        nimg = 0
        for it in spec:
            if it.get('skip'):
                continue
            h = [x for x in gidx if x['file'] == it['file'] and x['off'] == it['off'] and x['page'] == it['page']][0]['hash']
            locs = [loc for hh in [h] + near.get(it['key'], []) for loc in byhash[hh]]
            for loc in locs:
                f = loc['file']
                if f not in replaced:
                    replaced[f] = bytearray(open('work/dig/%04d.bin' % f, 'rb').read())
                patch_gim(replaced[f], dict(it, file=f, off=loc['off'], page=loc['page']))
                nimg += 1
        print('이미지', nimg, '곳 수정')

    # save-data / system texts (UTF-8 tables in dig 0012, members 3 and 5)
    sysd = json.load(open('translation/sys_strings.json', encoding='utf8'))
    from utf8tab import build as build_utf8
    d = replaced.setdefault(12, bytearray(open('work/dig/0012.bin', 'rb').read()))
    M12 = {m['id']: m for m in members(d)}
    for mid, strs in sysd.items():
        m = M12[int(mid)]
        d[m['off']:m['off'] + m['size']] = build_utf8(bytes(d[m['off']:m['off'] + m['size']]), strs)

    build_dig({k: bytes(v) for k, v in replaced.items()}, 'work/cfc_kr.dig')
    build_iso(SRC_ISO, 'work/cfc_kr.dig', out_iso)
    patch_sfo_title(out_iso, sysd['3'][1])
    print('완료', out_iso)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'Bleach - Soul Carnival 2 (Japan) [KR].iso')
