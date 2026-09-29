"""All structurally valid tables not yet in blocks.json whose strings use only valid glyph codes."""
import sys,glob,json;sys.path.insert(0,'tools')
from msgblk import find_blocks,strings
from table import dec
from multiprocessing import Pool
B=json.load(open('work/blocks.json')); have={(b['file'],b['base']) for b in B}
def job(p):
    f=int(p[-8:-4])
    if f in (34,4178,4184): return []
    d=open(p,'rb').read(); out=[]
    for b in find_blocks(d):
        if (f,b['base']) in have: continue
        S=strings(d,b)
        if any(0x712<=x<0x1000 or 0x1100<=x<0x8000 or x>=0x8200 for s in S for x in s): continue
        jp=sum(1 for s in S for x in s if 0x5e<=x<0x712)
        if jp==0: continue
        if sum(1 for s in S if len(s)==0)>len(S)*0.5: continue
        b['file']=f; b['strs']=S; out.append(b)
    return out
if __name__=='__main__':
    with Pool(4) as pool: R=pool.map(job,sorted(glob.glob('work/dig/*.bin')),chunksize=8)
    X=[b for r in R for b in r]
    json.dump(X,open('work/rest.json','w'))
    with open('work/rest.txt','w',encoding='utf8') as fo:
        for b in X: fo.write('%d %x %s n=%d | %s\n'%(b['file'],b['base'],b['kind'],b['n'],' | '.join(dec(s).replace('\n','/') for s in b['strs'][:8])[:200]))
    print(len(X))
