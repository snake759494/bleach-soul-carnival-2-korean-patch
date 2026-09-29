"""Message tables: at base p either
   A) u32 offs[n] with offs[0]==4n            (table starts at base)
   B) u32 n, u32 offs[n] with offs[0]==4+4n   (count at base)
 offsets relative to base, u16 glyph strings terminated by 0x8000."""
import struct,numpy as np
def find_blocks(d):
    out=[]; L=len(d)
    a=np.frombuffer(d[:L//4*4],'<u4')
    cand=[]
    for kind,cond in (('A',None),('B',None)):
        pass
    idx=np.arange(len(a))
    # A: a[i]==4n, n>=1, a[i+1]? ; B: a[i+1]==4+4*a[i]
    A=np.nonzero((a%4==0)&(a>=4)&(a<=4*20000))[0]
    B=np.nonzero((a[:-1]>=1)&(a[:-1]<=20000)&(a[1:]==4+4*a[:-1]))[0]
    seen=set()
    for kind,lst in (('B',B),('A',A)):
        for i in lst:
            p=4*int(i)
            if kind=='A': n=int(a[i])//4; to=p
            else: n=int(a[i]); to=p+4
            if to+4*n>L: continue
            offs=struct.unpack_from('<%dI'%n,d,to)
            if any(offs[k]>offs[k+1] for k in range(n-1)) or p+offs[-1]>=L: continue
            if kind=='A' and n<2: continue
            ok=True; ends=[]
            for k in range(n):
                s=p+offs[k]
                if s%2: ok=False;break
                lim=p+offs[k+1] if k+1<n and offs[k+1]>offs[k] else min(L,s+6000)
                j=s
                while j<lim and struct.unpack_from('<H',d,j)[0]!=0x8000: j+=2
                if j>=lim: ok=False;break
                ends.append(j+2)
            if not ok or p in seen: continue
            seen.add(p)
            out.append(dict(kind=kind,base=p,n=n,offs=list(offs),end=max(ends)))
    return out
def strings(d,b):
    res=[]
    for o in b['offs']:
        j=b['base']+o; seq=[]
        while True:
            c=struct.unpack_from('<H',d,j)[0]; j+=2
            if c==0x8000: break
            seq.append(c)
        res.append(seq)
    return res
