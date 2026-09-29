"""Extract every GIM image (all pages) to work/gim/<file>_<off>_<page>.png, dedup by pixel hash -> work/gim_index.json"""
import sys,glob,struct,json,hashlib,os,numpy as np;sys.path.insert(0,'tools')
from PIL import Image
from swz import unswizzle
from multiprocessing import Pool
def parse_gim(g):
    """yield (page, fmt, w, h, pixels_rgba)"""
    out=[]; pal=None
    def walk(p,end):
        nonlocal pal
        while p+16<=end:
            bid,_,size,nxt,dat=struct.unpack_from('<HHIII',g,p)
            if size<16 or p+size>len(g): return
            if bid in (2,3): walk(p+dat,p+size)
            elif bid in (4,5):
                h=p+dat; fmt,order,w,hh,bpp=struct.unpack_from('<HHHHH',g,h+4)
                doff=h+struct.unpack_from('<I',g,h+0x1c)[0]
                out.append((bid,fmt,order,w,hh,doff))
            p+=size
    walk(0x10,len(g)); return out
def decode(g,blocks):
    res=[]; pal=None
    for bid,fmt,order,w,h,doff in blocks:
        if bid==5:
            if fmt==3: pal=np.frombuffer(g[doff:doff+4*w*h],np.uint8).reshape(-1,4)
            elif fmt in (0,1,2):
                raw=np.frombuffer(g[doff:doff+2*w*h],'<u2').astype(np.uint32)
                if fmt==0: r=(raw&31)<<3;gg=((raw>>5)&63)<<2;b=((raw>>11)&31)<<3;a=np.full_like(r,255)
                elif fmt==1: r=(raw&31)<<3;gg=((raw>>5)&31)<<3;b=((raw>>10)&31)<<3;a=((raw>>15)&1)*255
                else: r=(raw&15)*17;gg=((raw>>4)&15)*17;b=((raw>>8)&15)*17;a=((raw>>12)&15)*17
                pal=np.stack([r,gg,b,a],1).astype(np.uint8)
            continue
        bpp={3:32,4:4,5:8}.get(fmt)
        if bpp is None: continue
        wb=(w*bpp+7)//8; wb_al=(wb+15)//16*16; h_al=(h+7)//8*8
        raw=g[doff:doff+wb_al*h_al]
        if len(raw)<wb_al*h_al: continue
        if order==1: raw=unswizzle(raw,wb_al,h_al)
        a=np.frombuffer(raw,np.uint8).reshape(h_al,wb_al)[:h,:wb]
        if fmt==3: img=a.reshape(h,w,4)
        elif pal is None: continue
        elif fmt==5: img=pal[np.clip(a,0,len(pal)-1)]
        else:
            idx=np.stack([a&15,a>>4],2).reshape(h,-1)[:,:w]; img=pal[np.clip(idx,0,len(pal)-1)]
        res.append(img)
    return res
def job(p):
    f=int(p[-8:-4]); d=open(p,'rb').read(); out=[]
    i=d.find(b'MIG.00.1PSP')
    while i>=0:
        try:
            bl=parse_gim(d[i:]); imgs=decode(d[i:],bl)
            for k,img in enumerate(imgs):
                hsh=hashlib.md5(img.tobytes()).hexdigest()[:16]
                fn='work/gim/%s.png'%hsh
                if not os.path.exists(fn): Image.fromarray(img,'RGBA').save(fn)
                out.append(dict(file=f,off=i,page=k,w=int(img.shape[1]),h=int(img.shape[0]),hash=hsh))
        except Exception as e: pass
        i=d.find(b'MIG.00.1PSP',i+1)
    return out
if __name__=='__main__':
    os.makedirs('work/gim',exist_ok=True)
    with Pool(4) as pool: R=pool.map(job,sorted(glob.glob('work/dig/*.bin')),chunksize=4)
    X=[x for r in R for x in r]; json.dump(X,open('work/gim_index.json','w'))
    print(len(X),'pages',len({x['hash'] for x in X}),'unique')
