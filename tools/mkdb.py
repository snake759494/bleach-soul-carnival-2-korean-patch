import sys,json,os,collections;sys.path.insert(0,'tools')
from table import dec
B=json.load(open('work/blocks.json'))
import os
order=[tuple(x) for x in json.load(open('work/uniq_codes.json'))] if os.path.exists('work/uniq_codes.json') else []
U={t:i for i,t in enumerate(order)}
old=len(order)
for b in B:
    for s in b['strs']:
        t=tuple(s)
        if t not in U: U[t]=len(order); order.append(t)
uniq=[dec(list(t)) for t in order]
json.dump([list(t) for t in order],open('work/uniq_codes.json','w'))
json.dump(uniq,open('translation/unique_ja.json','w',encoding='utf8'),ensure_ascii=False,indent=0)
os.makedirs('translation/batches',exist_ok=True); os.makedirs('translation/out',exist_ok=True)
N=160; k=(old+N-1)//N if old else 0
for i in range(old,len(uniq),N):
    json.dump([[j,uniq[j]] for j in range(i,min(i+N,len(uniq)))],open('translation/batches/b%03d.json'%k,'w',encoding='utf8'),ensure_ascii=False,indent=0); k+=1
print(len(uniq),'unique',k,'batches')
