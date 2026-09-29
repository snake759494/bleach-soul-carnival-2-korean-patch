"""usage: python tools/shrinkcheck.py s00 [s01 ...] | all  — checks translation/shrink/sNN_out.json"""
import sys,json,glob,os,re
sys.path.insert(0,os.path.dirname(__file__))
from check import check,ROOT
TOK=re.compile(r'\{[0-9A-F]{4}\}')
def klen(t):
    t=t.replace('\n','{8010}'); return len(TOK.findall(t))+len(TOK.sub('',t))
def run(n):
    src=json.load(open(os.path.join(ROOT,'translation/shrink/%s.json'%n),encoding='utf8'))
    p=os.path.join(ROOT,'translation/shrink/%s_out.json'%n)
    if not os.path.exists(p): print(n,'없음'); return len(src)
    out=json.load(open(p,encoding='utf8')); bad=0
    for x in src:
        ko=out.get(str(x['id']))
        if ko is None: print(n,x['id'],'누락'); bad+=1; continue
        e=check(x['id'],x['ja'],ko)
        L=klen(ko)
        if L>x['max']: e.append('길이 %d > 목표 %d'%(L,x['max']))
        if e: bad+=1; print(n,x['id'],'|',ko.replace(chr(10),'\n'),'|',' / '.join(e))
    print(n,'오류',bad,'/',len(src)); return bad
if __name__=='__main__':
    names=sys.argv[1:]
    if names==['all']: names=sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT,'translation/shrink/s??.json')))
    print('총 오류',sum(run(n) for n in names))
