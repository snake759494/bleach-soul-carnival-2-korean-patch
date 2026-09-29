import sys,numpy as np;sys.path.insert(0,'tools')
from ppsspp_rpc import Debugger,readmem
def dump(path='work/ram.bin'):
    d=Debugger(); m=readmem(d,0x08800000,0x1800000); open(path,'wb').write(m); return m
def search(m,w):
    e=w.encode('euc_jp'); jis=[((e[i]&0x7f)<<8)|(e[i+1]&0x7f) for i in range(0,len(e),2)]
    sj=w.encode('cp932'); sjis=[(sj[i]<<8)|sj[i+1] for i in range(0,len(sj),2)]
    uni=[ord(c) for c in w]; n=len(uni)
    for al in (0,1):
      for end in ('<','>'):
        a=np.frombuffer(m[al:al+(len(m)-al)//2*2],dtype=end+'u2').astype(np.int32)
        for name,codes in (('jis',jis),('sjis',sjis),('uni',uni)):
            c=np.ones(len(a)-n,bool)
            for k in range(n-1): c&=(a[k+1:len(a)-n+k+1]-a[k:len(a)-n+k])==codes[k+1]-codes[k]
            for i in np.nonzero(c)[0][:8]: print(w,name,al,end,hex(0x08800000+al+2*i),'val',hex(a[i]),'code',hex(codes[0]))
    # byte-level: sjis bytes, utf8
    for name,b in (('sjisb',w.encode('cp932')),('u8',w.encode())):
        i=m.find(b)
        if i>=0: print(w,name,hex(0x08800000+i))
if __name__=='__main__':
    m=dump() if sys.argv[1]=='dump' else open('work/ram.bin','rb').read()
    for w in sys.argv[2:]: search(m,w)
