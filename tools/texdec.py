import struct
from swz import unswizzle
from PIL import Image
def blocks_textures(d,p):
    hs,doff,coff,nn,nt=struct.unpack_from('<5I',d,p+4)
    out=[]
    for i in range(nt):
        po,wh,stride,sz,z=struct.unpack_from('<5I',d,p+doff+20*i)
        co=struct.unpack_from('<I',d,p+coff+4*i)[0]
        rec=d[p+0x18+12*i:p+0x18+12*i+12]
        out.append(dict(i=i,pix=p+po,w=wh&0xffff,h=wh>>16,stride=stride,size=sz,clut=p+co,rec=rec))
    return out
def decode(d,t):
    w,h,sz=t['w'],t['h'],t['size']; st=t['stride'] or w
    bpp=sz*8//(st*h) if st*h else 8
    raw=d[t['pix']:t['pix']+sz]
    bw=st*bpp//8
    try: raw=unswizzle(raw,bw,h)
    except Exception: pass
    ncol=16 if bpp==4 else 256
    cl=d[t['clut']:t['clut']+4*ncol]
    pal=[tuple(cl[4*k:4*k+4]) for k in range(len(cl)//4)]
    while len(pal)<ncol: pal.append((0,0,0,0))
    im=Image.new('RGBA',(st,h))
    if bpp==8: idx=raw
    else:
        idx=[]
        for x in raw: idx+=[x&15,x>>4]
    im.putdata([pal[v] for v in idx[:st*h]])
    return im.crop((0,0,w,h))
