"""Compute per-string max length (u16 units incl. terminator) so every pool fits. -> translation/shrink/sNN.json"""
import sys,json,glob,re,os,math,collections;sys.path.insert(0,'tools')
from pressure import klen,tr
P=json.load(open('work/pressure.json'))
tgt={}
for x in P:
    R=math.ceil(x['over']*1.05)+2
    L={i:klen(tr[i]) for i in x['ids']}
    w={i:max(0,L[i]-12) for i in x['ids']}
    W=sum(w.values())
    for i in x['ids']:
        if w[i]==0: continue
        cut=math.ceil(R*w[i]/W)
        t=max(L[i]-cut,8)
        tgt[i]=min(tgt.get(i,10**9),t)
cur={i:klen(tr[i]) for i in tgt}
items=sorted(i for i in tgt if tgt[i]<cur[i])
ja=json.load(open('translation/unique_ja.json',encoding='utf8'))
os.makedirs('translation/shrink',exist_ok=True)
for f in glob.glob('translation/shrink/*.json'): os.remove(f)
N=250
for k in range(0,len(items),N):
    json.dump([dict(id=i,ja=ja[i],ko=tr[i],max=tgt[i]-1,now=cur[i]-1) for i in items[k:k+N]],open('translation/shrink/s%02d.json'%(k//N),'w',encoding='utf8'),ensure_ascii=False,indent=0)
json.dump({str(i):tgt[i]-1 for i in items},open('work/targets.json','w'))
print(len(items),'strings, files',math.ceil(len(items)/N))
print('avg cut %.1f%%'%(100*sum(cur[i]-tgt[i] for i in items)/sum(cur[i] for i in items)))
