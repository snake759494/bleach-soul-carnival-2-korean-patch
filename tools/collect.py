import sys,glob,json;sys.path.insert(0,'tools')
from msgblk import find_blocks,strings
from scan2 import good
from multiprocessing import Pool
def job(p):
    d=open(p,'rb').read(); out=[]
    for b in find_blocks(d):
        S=strings(d,b)
        if any(0x712<=x<0x1000 or 0x1100<=x<0x8000 or x>=0x8200 for s in S for x in s): continue
        g=sum(1 for s in S if good(s))
        hi=sum(1 for s in S if sum(1 for x in s if 0x5e<=x<0x712)>=2)
        f=int(p[-8:-4])
        if f in (34,4178,4184): continue
        if g>=max(1,len(S)*0.3) or (b['n']>=2 and hi>=len(S)*0.5):
            b['file']=int(p[-8:-4]); b['strs']=S; out.append(b)
    return out
if __name__=='__main__':
    with Pool(4) as pool: R=pool.map(job,sorted(glob.glob('work/dig/*.bin')),chunksize=8)
    B=[b for r in R for b in r]
    json.dump(B,open('work/blocks.json','w'))
    print(len(B),'blocks', len(set(b['file'] for b in B)),'files', sum(b['n'] for b in B),'strings')
