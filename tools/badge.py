"""Redraw the red kanji badges in the icon atlas (dig 0002 member 3, cells 0x1028-0x102B) as Hangul."""
import sys,numpy as np;sys.path.insert(0,'tools')
from PIL import Image,ImageDraw,ImageFont
from gim import pages,page_pixels,palette
from swz import swizzle
BADGES={0x28:'파',0x29:'가',0x2a:'사',0x2b:'호'}  # 破面/仮面/死神/虚
def patch(g):
    g=bytearray(g); e=pages(bytes(g))[0]; px=page_pixels(bytes(g),e).copy(); pal=palette(bytes(g),e).astype(np.float32)
    f=ImageFont.truetype('NanumSquareNeo-eHv.ttf',15)
    for cell,ch in BADGES.items():
        r,c=divmod(cell,16); y0,x0=r*16,c*16
        orig=pal[px[y0:y0+16,x0:x0+16]]
        # per-row fill colour from the original's opaque pixels
        rows=[]
        for y in range(16):
            m=orig[y,:,3]>200
            rows.append(orig[y,m,:3].mean(0) if m.any() else None)
        last=np.array([120,20,20],np.float32)
        for y in range(16):
            if rows[y] is None: rows[y]=last
            last=rows[y]
        im=Image.new('L',(16,16)); ImageDraw.Draw(im).text((8,8),ch,font=f,fill=255,anchor='mm')
        a=np.asarray(im,np.float32)
        # 1px dark outline like the original
        o=np.zeros_like(a)
        for dy in (-1,0,1):
            for dx in (-1,0,1): o=np.maximum(o,np.roll(np.roll(a,dy,0),dx,1))
        out=np.zeros((16,16,4),np.float32)
        for y in range(16):
            col=rows[y]
            out[y,:,:3]=col[None,:]*(a[y,:,None]/255)+np.array([20,10,10])*(1-a[y,:,None]/255)
        out[:,:,3]=np.maximum(a,o*0.9)
        # quantize to palette (RGBA distance)
        flat=out.reshape(-1,4); dist=((flat[:,None,:]-pal[None,:,:])**2).sum(2)
        px[y0:y0+16,x0:x0+16]=dist.argmin(1).reshape(16,16).astype(np.uint8)
    im=e[4]; g[im['data']:im['data']+px.size]=swizzle(px.tobytes(),px.shape[1],px.shape[0])
    return bytes(g)
