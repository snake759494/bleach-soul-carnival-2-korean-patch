"""Patch text in GIM pages inside dig entries.
spec item: {"file":F,"off":GIM offset,"page":k,"boxes":[[x0,y0,x1,y1],...] or null(auto),"texts":[...],"font":opt}"""
import sys,os,struct,numpy as np
sys.path.insert(0,os.path.dirname(__file__))
from PIL import Image
from gimdump import parse_gim,decode
from swz import swizzle,unswizzle
import imgloc
from PIL import ImageDraw,ImageFont
BOLD=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),'NanumSquareNeo-cBd.ttf')
def lum(a): return a[...,0]*0.299+a[...,1]*0.587+a[...,2]*0.114
def flat_render(im,box,text,force=None,style=None):
    """small labels: per-row background from the box's edge columns, ink = pixels far from it"""
    A=np.array(im).astype(float); x0,y0,x1,y1=box; H=y1-y0; W=x1-x0
    sub=A[y0:y1,x0:x1]; op=sub[...,3]>128
    edge=np.zeros((H,W),bool); edge[:,:2]=True; edge[:,-2:]=True
    bgrow=[]; transparent=0
    for y in range(H):
        m=edge[y]&op[y]
        if m.sum()>=2: bgrow.append(np.median(sub[y][m],0))
        else: bgrow.append(None); transparent+=1
    last=next((c for c in bgrow if c is not None),np.array([0,0,0,0.]))
    for y in range(H):
        if bgrow[y] is None: bgrow[y]=last
        last=bgrow[y]
    BG=np.stack(bgrow)[:,None,:]
    dist=np.abs(sub[...,:3]-BG[...,:3]).sum(2)*op
    if (dist>0).sum()>4:
        t=np.percentile(dist[op],70); inkc=np.median(sub[(dist>=t)&op],0)
    else: inkc=np.array([255,255,255,255.])
    Hh,Ww=A.shape[:2]
    ring=A[max(0,y0-3):min(Hh,y1+3),max(0,x0-3):min(Ww,x1+3)][...,3].copy()
    ry,rx=y0-max(0,y0-3),x0-max(0,x0-3)
    inner=np.zeros(ring.shape,bool); inner[ry:ry+H,rx:rx+W]=True
    ec=sub[:,list(range(min(3,W)))+list(range(max(0,W-3),W))]
    eo=ec[...,3]>128
    button=eo.mean()>0.6
    on_transparent=not button
    if force=='glow': on_transparent=True
    elif force=='flat': on_transparent=False
    out=A.copy()
    if on_transparent: out[max(0,y0-2):y1+2,max(0,x0-2):x1+2]=0
    else:
        # inpaint only the ink (pixels far from the row background), keeping texture/gradients
        t=np.percentile(dist[op],55) if op.any() else 0
        ink=(dist>max(t,40))&op
        from scipy.ndimage import binary_dilation
        ink=binary_dilation(ink,iterations=1)&op
        blk=sub.copy(); known=~ink
        blk[ink]=np.broadcast_to(BG,sub.shape)[ink]
        for _ in range(40):
            acc=np.zeros_like(blk); cnt=np.zeros(blk.shape[:2])
            for dy,dx in ((1,0),(-1,0),(0,1),(0,-1)):
                sh=np.roll(np.roll(blk,dy,0),dx,1); k=np.roll(np.roll(known,dy,0),dx,1)
                acc+=sh*k[...,None]; cnt+=k
            upd=ink&(cnt>0)
            blk[upd]=acc[upd]/cnt[upd][:,None]
            known=known|upd
        blk[...,3]=sub[...,3]
        out[y0:y1,x0:x1]=blk
    base=Image.fromarray(np.clip(out,0,255).astype(np.uint8),'RGBA')
    import label
    st_=style or {}
    m=label.text_mask(text,max(1,W-2),H,st_.get('font','bold'),st_.get('italic',0.0))
    mm=np.zeros((H,W),np.float32); mm[:,1:1+m.shape[1]]=m
    mask=Image.fromarray((mm*255).astype(np.uint8))
    layer=Image.new('RGBA',(W,H),(0,0,0,0))
    if on_transparent:
        from PIL import ImageFilter
        dk=sub[op]; dk=dk[np.argsort(dk[:,:3].sum(1))[:max(1,len(dk)//5)]] if len(dk) else np.array([[0,0,0,255.]])
        oc=tuple(int(v) for v in np.median(dk,0)[:3])
        if not (style or {}).get('outline') and not (style or {}).get('plain'):
            glow=mask.filter(ImageFilter.MaxFilter(5)).point(lambda v: v*0.55)
            layer.paste(Image.new('RGBA',(W,H),oc+(255,)),(0,0),glow)
            layer.paste(Image.new('RGBA',(W,H),oc+(255,)),(0,0),mask.filter(ImageFilter.MaxFilter(3)))
        inkc=np.array([255,255,255,255.]) if inkc[:3].mean()<128 else inkc
    style=style or {}
    if style.get('ink'): inkc=np.array(list(style['ink'])+[255.])
    if style.get('outline'):
        from PIL import ImageFilter
        layer.paste(Image.new('RGBA',(W,H),tuple(style['outline'])+(255,)),(0,0),mask.filter(ImageFilter.MaxFilter(3)))
    elif not on_transparent:
        from PIL import ImageFilter
        bgl=float(lum(BG[:,0,:3]).mean()); inl=float(lum(inkc[None,:3])[0])
        if abs(bgl-inl)<110:
            oc=(255,255,255) if inl<bgl else (20,20,20)
            layer.paste(Image.new('RGBA',(W,H),oc+(255,)),(0,0),mask.filter(ImageFilter.MaxFilter(3)))
    layer.paste(Image.new('RGBA',(W,H),tuple(int(v) for v in inkc[:3])+(255,)),(0,0),mask)
    base.alpha_composite(layer,(x0,y0))
    return base


def page_info(g,page):
    bl=parse_gim(g); pal=None; k=0
    for b in bl:
        bid,fmt,order,w,h,doff=b
        if bid==5: pal=b; continue
        if fmt not in (3,4,5): continue
        if k==page: return b,pal
        k+=1
    raise IndexError(page)
def palette_rgba(g,pb):
    bid,fmt,order,w,h,doff=pb
    assert fmt==3
    return [tuple(g[doff+4*i:doff+4*i+4]) for i in range(w*h)]
def patch(d,item):
    """d: bytearray of whole dig entry"""
    o=item['off']; g=bytes(d[o:])
    imgs=decode(g,parse_gim(g)); im=Image.fromarray(imgs[item['page']],'RGBA')
    (bid,fmt,order,w,h,doff),pb=page_info(g,item['page'])
    boxes=item.get('boxes') or imgloc.regions(im)
    texts=item['texts']
    if len(boxes)!=len(texts): raise Exception('boxes %s vs texts %d in %s'%(boxes,len(texts),item))
    new=im.copy()
    modes=item.get('modes') or [None]*len(boxes)
    styles=item.get('styles') or [None]*len(boxes)
    for box,tx,md,sty in zip(boxes,texts,modes,styles):
        if tx is None: continue
        x0,y0,x1,y1=box
        if md in ('glow','outline','plain','plate'):
            import label
            new=label.draw(new,box,tx,md,[b for b in boxes if b is not box],sty); continue
        if md=='button': md='flat'
        if item.get('mode','flat')=='flat':
            new=flat_render(new,box,tx,md,sty); continue
        st=imgloc.style(im,box)
        clear=item.get('clear',[0,0,0,0])
        new.paste(Image.new('RGBA',(x1-x0+4,y1-y0+4),tuple(clear)),(x0-2,y0-2))
        new.alpha_composite(imgloc.render_text(tx,box,st,item.get('font',imgloc.FONT)),(x0,y0))
    bpp={4:4,5:8,3:32}[fmt]
    wb=(w*bpp+7)//8; wb_al=(wb+15)//16*16; h_al=(h+7)//8*8
    raw=bytearray(g[doff:doff+wb_al*h_al])
    lin=bytearray(unswizzle(bytes(raw),wb_al,h_al) if order==1 else raw)
    A=np.frombuffer(bytes(lin),np.uint8).reshape(h_al,wb_al).copy()
    if fmt==3:
        A[:h,:w*4]=np.array(new).reshape(h,w*4)
    else:
        pal=palette_rgba(g,pb)
        if fmt==4: pal=pal[:16]
        q=imgloc.quantise(new,pal).reshape(h,w)
        if fmt==5: A[:h,:w]=q
        else:
            packed=(q[:, 0::2] | (q[:, 1::2]<<4)) if w%2==0 else None
            A[:h,:w//2]=packed
    out=A.tobytes()
    if order==1: out=swizzle(out,wb_al,h_al)
    d[o+doff:o+doff+len(out)]=out
    return new
