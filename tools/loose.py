"""Loose strings outside known tables: runs of glyph codes ending in 0x8000, starting after a terminator or zero word."""
import sys,glob,json,numpy as np;sys.path.insert(0,'tools')
from table import TAB,dec
from multiprocessing import Pool
ocr=json.load(open('work/ocr_raw.json',encoding='utf8'))
GOOD=np.zeros(0x10000,bool)
for i in range(0x712):
    if i<0x5e or ocr[i][0]>0.75: GOOD[i]=True
GOOD[0x8001:0x8100]=True; GOOD[0x1000:0x1040]=True
B=json.load(open('work/blocks.json'))+json.load(open('work/rest.json'))
rng={}
for b in B:
    s=min(b['base']+o for o in b['offs']); rng.setdefault(b['file'],[]).append((b['base'],b['end']))
def job(p):
    f=int(p[-8:-4])
    if f in (34,4178,4184): return []
    d=open(p,'rb').read(); a=np.frombuffer(d[:len(d)//2*2],'<u2')
    ends=np.nonzero(a==0x8000)[0]; out=[]
    for e in ends:
        s=e
        while s>0 and a[s-1]!=0x8000 and a[s-1]!=0 and GOOD[a[s-1]] and e-s<200: s-=1
        # a[s-1] must be terminator or zero (boundary)
        if s==0 or a[s-1] not in (0x8000,0): continue
        seq=a[s:e]
        if len(seq)==0: continue
        jp=((seq>=0x5e)&(seq<0x712)).sum()
        if jp==0: continue
        off=2*s
        if any(x<=off<y for x,y in rng.get(f,[])): continue
        out.append((f,int(off),[int(v) for v in seq]))
    return out
if __name__=='__main__':
    with Pool(4) as pool: R=pool.map(job,sorted(glob.glob('work/dig/*.bin')),chunksize=8)
    X=[x for r in R for x in r]
    json.dump(X,open('work/loose.json','w'))
    with open('work/loose.txt','w',encoding='utf8') as fo:
        for f,o,s in X: fo.write('%d %x %s\n'%(f,o,dec(s).replace('\n','/')))
    print(len(X))
