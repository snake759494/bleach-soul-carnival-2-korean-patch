"""For each image spec, find visually near-identical pages (same size, mean abs RGBA diff < 10) -> work/neardup.json {key:[{file,off,page,hash}]}"""
import json,numpy as np
from PIL import Image
X=json.load(open('work/gim_index.json'))
import glob
spec=[x for p in sorted(glob.glob('translation/images_part*.json')) for x in json.load(open(p,encoding='utf8'))]
bysize={}
first={}
for x in X: first.setdefault(x['hash'],x)
for x in first.values(): bysize.setdefault((x['w'],x['h']),[]).append(x)
cache={}
def arr(h):
    if h not in cache: cache[h]=np.asarray(Image.open('work/gim/%s.png'%h).convert('RGBA'),np.float32)
    return cache[h]
res={}
for it in spec:
    if it.get('skip'): continue
    src=[x for x in X if x['file']==it['file'] and x['off']==it['off'] and x['page']==it['page']][0]
    a=arr(src['hash']); hits=[]
    for y in bysize.get((src['w'],src['h']),[]):
        if y['hash']==src['hash']: continue
        b=arr(y['hash'])
        if np.abs(a-b).mean()<10: hits.append(y['hash'])
    if hits: res[it['key']]=hits
json.dump(res,open('work/neardup.json','w'),indent=0)
print(len(res),'specs have near-duplicates;', sum(len(v) for v in res.values()),'extra pages')
