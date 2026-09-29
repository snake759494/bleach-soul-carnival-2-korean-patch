"""Render patched images for review: python tools/imgtest.py KEY [KEY...] | all  -> work/imgout/KEY.png (before|after, 2x)"""
import sys,json,os;sys.path.insert(0,'tools')
from PIL import Image
from gimpatch import patch
from gimdump import parse_gim,decode
spec={x['key']:x for x in json.load(open(os.environ.get('IMGSPEC','translation/images.json'),encoding='utf8'))}
os.makedirs('work/imgout',exist_ok=True)
keys=list(spec) if sys.argv[1:]==['all'] else sys.argv[1:]
for k in keys:
    it=spec[k]
    if it.get('skip'): continue
    d=bytearray(open('work/dig/%04d.bin'%it['file'],'rb').read())
    g=bytes(d[it['off']:]); before=Image.fromarray(decode(g,parse_gim(g))[it['page']],'RGBA')
    try: patch(d,it)
    except Exception as e: print(k,'ERROR',e); continue
    g=bytes(d[it['off']:]); after=Image.fromarray(decode(g,parse_gim(g))[it['page']],'RGBA')
    W,H=before.size; s=2 if max(W,H)<=512 else 1
    out=Image.new('RGBA',(W*2*s+8,H*s),(40,40,90,255))
    for i,im in enumerate((before,after)):
        bg=Image.new('RGBA',im.size,(40,40,90,255)); bg.alpha_composite(im); out.paste(bg.resize((W*s,H*s),Image.NEAREST),(i*(W*s+8),0))
    out.save('work/imgout/%s.png'%k); print(k,'ok')
