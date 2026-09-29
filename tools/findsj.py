import glob,sys,numpy as np
def issj(c): 
    h=c>>8; l=c&0xff
    return (0x81<=h<=0x9f or 0xe0<=h<=0xea) and (0x40<=l<=0xfc and l!=0x7f)
paths=sys.argv[1:] or sorted(glob.glob('work/dig/*.bin'))+['work/eboot_plain.bin']
for p in paths:
    d=open(p,'rb').read()
    for end in ('<','>'):
        a=np.frombuffer(d[:len(d)//2*2],dtype=end+'u2')
        h=a>>8; l=a&0xff
        ok=(((h>=0x81)&(h<=0x9f))|((h>=0xe0)&(h<=0xea)))&(l>=0x40)&(l<=0xfc)
        # runs
        idx=np.nonzero(np.diff(np.concatenate(([0],ok.astype(np.int8),[0]))))[0]
        for s,e in zip(idx[::2],idx[1::2]):
            if e-s>=100 and len(set(a[s:e].tolist()))>(e-s)*0.8:
                txt=bytes(a[s:s+20].astype('>u2').tobytes()).decode('cp932','replace')
                print(p,end,hex(s*2),e-s,txt)
