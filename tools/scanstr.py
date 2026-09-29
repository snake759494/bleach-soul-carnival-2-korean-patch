import glob,sys,numpy as np,json,collections
NG=0x710
def scan(d,minlen=3):
    out=[]
    for al in (0,):
        a=np.frombuffer(d[al:al+(len(d)-al)//2*2],'<u2')
        ok=(a<NG)|((a>=0x8000)&(a<0x8100))
        idx=np.nonzero(np.diff(np.concatenate(([0],ok.astype(np.int8),[0]))))[0]
        for s,e in zip(idx[::2],idx[1::2]):
            seg=a[s:e]; ends=np.nonzero(seg==0x8000)[0]
            st=0
            for t in ends:
                sub=seg[st:t]
                if len(sub)>=minlen and (sub>=0x5e).sum()>=2 and (sub<0x8000).sum()>=2: out.append((al+2*(s+st),sub.tolist()))
                st=t+1
    return out
if __name__=='__main__':
    res={}
    for p in sorted(glob.glob('work/dig/*.bin')):
        d=open(p,'rb').read(); r=scan(d)
        if len(r)>=3: res[p[-8:-4]]=len(r)
    print(len(res),sum(res.values()))
    json.dump(res,open('work/strcount.json','w'))
    print(sorted(res.items(),key=lambda x:-x[1])[:60])
