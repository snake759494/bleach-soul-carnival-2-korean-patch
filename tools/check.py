"""Validate translation/out/bNNN.json against batches. usage: python tools/check.py b000 [b001 ...]  (or 'all')"""
import sys,json,re,glob,os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0,os.path.dirname(__file__))
from member import members
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d=open(os.path.join(ROOT,'work/dig/0002.bin'),'rb').read(); M=members(d)
W=d[M[4]['off']:M[4]['off']+M[4]['size']]
U=json.load(open(os.path.join(ROOT,'work/uniq_codes.json')))
SYM=set('♀♂―…、。!?「」『』()・~♪★☆※×○●◆◇△▲▼→←↑↓%+-:/.,\'"#&*=<>[]_ 0123456789')
TOK=re.compile(r'\{[0-9A-F]{4}\}')
# icon-atlas cells that are kanji, not buttons: must be written out in Korean
KICON={'{%04X}'%c for c in list(range(0x1011,0x101B))+[0x1022,0x102C,0x102D]}
def kwidth(s):
    w=0
    for ch in s:
        o=ord(ch)
        if ch=='.': w+=W[0x0C]
        elif ch==',': w+=5
        elif 0x20<=o<0x7f: w+=W[o-0x20 if o<=0x5e else o-0x21]
        else: w+=15
    return w
def olines(codes):
    out=[[]]
    for c in codes:
        if c in (0x8001,0x8010): out.append([])
        else: out[-1].append(c)
    return out
def owidth(l): return sum(W[c] if c<0x712 else 15 for c in l if c<0x8000)
def klines(t):
    t=t.replace('\n','{8010}')
    return re.split(r'\{8001\}|\{8010\}',t)
def check(i,ja,ko):
    errs=[]
    codes=U[i]
    tj=sorted(TOK.findall(ja.replace('\n','')))
    tk=sorted(TOK.findall(ko.replace('\n','')))
    tj2=[t for t in tj if t!='{8001}' and t not in KICON]; tk2=[t for t in tk if t!='{8001}' and t not in KICON]
    if any(t in KICON for t in tk): errs.append('한자 아이콘 코드 %s 는 한글로 바꿔 써야 함'%[t for t in tk if t in KICON])
    if tj2!=tk2: errs.append('제어코드 불일치 %s vs %s'%(tj2,tk2))
    for ch in TOK.sub('',ko).replace('\n',''):
        if '\uac00'<=ch<='\ud7a3' or 0x20<=ord(ch)<0x7f or ch in SYM: continue
        errs.append('허용되지 않는 문자 %r'%ch); break
    ol=olines(codes); kl=klines(ko)
    dialog=any(c==0x8029 or 0x8100<=c<0x8200 for c in codes)
    if len(kl)>max(len(ol),1)+(1 if dialog and len(ol)<3 else 0): errs.append('줄 수 초과 %d>%d'%(len(kl),len(ol)))
    for k,l in enumerate(kl):
        w=kwidth(TOK.sub('',l))
        ow=owidth(ol[k]) if k<len(ol) else 0
        lim=max(ow,390) if dialog else max(ow,15)
        if w>lim: errs.append('%d번째 줄 폭 초과 %dpx>%dpx (%s)'%(k+1,w,lim,TOK.sub('',l)))
    return errs
def run(name):
    src=json.load(open(os.path.join(ROOT,'translation/batches/%s.json'%name),encoding='utf8'))
    p=os.path.join(ROOT,'translation/out/%s.json'%name)
    if not os.path.exists(p): print(name,'없음'); return 1
    out=json.load(open(p,encoding='utf8')); bad=0
    for i,ja in src:
        ko=out.get(str(i))
        if ko is None: print(name,i,'누락'); bad+=1; continue
        e=check(i,ja,ko)
        if e: bad+=1; print(name,i,'|',ja.replace('\n','\n'),'=>',ko.replace('\n','\n'),'|',' / '.join(e))
    print(name,'오류',bad,'/',len(src)); return bad
if __name__=='__main__':
    names=sys.argv[1:]
    if names==['all']: names=sorted(os.path.basename(p)[:-5] for p in glob.glob(os.path.join(ROOT,'translation/batches/*.json')))
    tot=sum(run(n) for n in names); print('총 오류',tot)
