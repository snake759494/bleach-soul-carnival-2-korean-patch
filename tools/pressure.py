"""Per pool: original capacity vs Korean size (u16 units). Writes work/pressure.json"""
import sys,json,glob,re,collections;sys.path.insert(0,'tools')
TOK=re.compile(r'\{[0-9A-F]{4}\}')
U=json.load(open('work/uniq_codes.json')); idx={tuple(s):i for i,s in enumerate(U)}
tr={}
for p in glob.glob('translation/out/b*.json'):
    for k,v in json.load(open(p,encoding='utf8')).items(): tr[int(k)]=v
def klen(t):  # u16 count incl terminator
    t=t.replace('\n','{8010}'); return len(TOK.findall(t))+len(TOK.sub('',t))+1
B=json.load(open('work/blocks.json'))
res=[]; tot=0
for b in B:
    cap=(b['end']-min(b['base']+o for o in b['offs']))//2
    ids=list(dict.fromkeys(idx[tuple(s)] for s in b['strs']))
    need=sum(klen(tr.get(i,'')) for i in ids)
    if need>cap: res.append(dict(file=b['file'],base=b['base'],cap=cap,need=need,over=need-cap,ids=ids)); tot+=need-cap
json.dump(res,open('work/pressure.json','w'))
print('초과 풀',len(res),'총 초과 u16',tot)
r=sorted(res,key=lambda x:-x['over']/x['cap'])
for x in r[:10]: print(x['file'],x['cap'],x['need'],'%.1f%%'%(100*x['over']/x['cap']))
# ids involved and their required shrink ratio
ratio=collections.defaultdict(float)
for x in res:
    for i in x['ids']: ratio[i]=max(ratio[i],x['over']/x['cap'])
print('관련 문자열',len(ratio), '최대 필요 축소율 %.1f%%'%(100*max(ratio.values())))
