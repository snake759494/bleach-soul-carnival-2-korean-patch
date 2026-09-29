import sys,json,glob;sys.path.insert(0,'tools')
from scanstr import scan
from scan2 import good
from table import dec
from multiprocessing import Pool
B=json.load(open('work/blocks.json'))
rng={}
for b in B:
    rng.setdefault(b['file'],[]).append((b['base'],b['base']+max(b['offs'])+2*len(b['strs'][-1])+2+4000))
def job(p):
    f=int(p[-8:-4]); d=open(p,'rb').read()
    r=[(o,s) for o,s in scan(d,2) if good(s) and len(s)>=4]
    r=[(o,s) for o,s in r if not any(a<=o<e for a,e in rng.get(f,[]))]
    return f,r
if __name__=='__main__':
    with Pool(4) as pool: R=pool.map(job,sorted(glob.glob('work/dig/*.bin')),chunksize=8)
    R=[x for x in R if len(x[1])>=3]
    print(len(R),sum(len(x[1]) for x in R))
    with open('work/uncovered.txt','w',encoding='utf8') as fo:
        for f,r in R:
            fo.write('== %04d %d\n'%(f,len(r)))
            for o,s in r[:8]: fo.write('%x %s\n'%(o,dec(s).replace('\n','/')))
