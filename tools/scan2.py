import glob,sys,json,numpy as np;sys.path.insert(0,'tools')
from scanstr import scan
from table import TAB,dec
KANA=np.zeros(0x8100,bool)
for i,c in enumerate(TAB):
    if 'ぁ'<=c<='ヿ' or c in '。、！？…「」ー': KANA[i]=True
def good(s):
    a=np.array(s); a=a[a<0x8000]
    return len(a)>=2 and KANA[a].mean()>=0.3
if __name__=='__main__':
    res={}
    for p in sorted(glob.glob('work/dig/*.bin')):
        d=open(p,'rb').read(); r=[x for x in scan(d,2) if good(x[1])]
        if r: res[p[-8:-4]]=(len(r),hex(r[0][0]),hex(r[-1][0]))
    json.dump(res,open('work/textfiles.json','w'),indent=0)
    print(len(res),sum(v[0] for v in res.values()))
    for k,v in res.items(): print(k,v)
