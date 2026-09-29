"""Refine OCR: top-k candidates by bbox features, then shifted raw correlation at several sizes/fonts."""
import sys,json,numpy as np
from PIL import Image,ImageDraw,ImageFont
import os
G=np.load(os.environ.get('GLYPHS','work/glyphs.npy'))
cands=[chr(c) for c in range(0x21,0x7f)]
for hi in list(range(0x81,0xa0))+list(range(0xe0,0xeb)):
    for lo in range(0x40,0xfd):
        try: cands.append(bytes([hi,lo]).decode('cp932'))
        except: pass
cands=list(dict.fromkeys(c for c in cands if len(c)==1))
fonts=['C:/Windows/Fonts/msgothic.ttc','C:/Windows/Fonts/meiryo.ttc','C:/Windows/Fonts/YuGothM.ttc','C:/Windows/Fonts/BIZ-UDGothicR.ttc','C:/Windows/Fonts/NotoSansJP-VF.ttf']
def render(ch,f):
    im=Image.new('L',(24,24)); ImageDraw.Draw(im).text((4,4),ch,font=f,fill=255); return np.asarray(im,np.float32)/255
def feat(a,n=12):
    ys,xs=np.nonzero(a>0.25)
    if len(ys)==0: return np.zeros(n*n+4,np.float32)
    y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    im=Image.fromarray((a[y0:y1,x0:x1]*255).astype(np.uint8)).resize((n,n),Image.BILINEAR)
    v=np.asarray(im,np.float32).ravel()/255; v=v-v.mean(); v/=(np.linalg.norm(v)+1e-6)
    return np.concatenate([v,np.array([(y1-y0)/16,(x1-x0)/16,(y0+y1)/32,(x0+x1)/32],np.float32)*0.6])
def crop(a):
    ys,xs=np.nonzero(a>0.25)
    if len(ys)==0: return None
    return a[ys.min():ys.max()+1,xs.min():xs.max()+1]
def pixcorr(g,r):
    """align bounding boxes (top-left) with small shifts, no resizing; penalize size mismatch"""
    cg=crop(g); cr=crop(r)
    if cg is None or cr is None: return -1
    H=max(cg.shape[0],cr.shape[0])+4; W=max(cg.shape[1],cr.shape[1])+4
    A=np.zeros((H,W),np.float32); A[2:2+cg.shape[0],2:2+cg.shape[1]]=cg
    best=-1
    for dy in range(-2,3):
        for dx in range(-2,3):
            B=np.zeros((H,W),np.float32)
            y=2+dy+(cg.shape[0]-cr.shape[0])//2; x=2+dx+(cg.shape[1]-cr.shape[1])//2
            if y<0 or x<0 or y+cr.shape[0]>H or x+cr.shape[1]>W: continue
            B[y:y+cr.shape[0],x:x+cr.shape[1]]=cr
            a=A.ravel()-A.mean(); b=B.ravel()-B.mean()
            c=float(a@b/(np.linalg.norm(a)*np.linalg.norm(b)+1e-6))
            best=max(best,c)
    return best

def canvas(a,N=20):
    """place crop centered on NxN canvas"""
    c=crop(a); out=np.zeros((N,N),np.float32)
    if c is None: return out,(0,0)
    h,w=min(c.shape[0],N),min(c.shape[1],N); y=(N-h)//2; x=(N-w)//2
    out[y:y+h,x:x+w]=c[:h,:w]; return out,c.shape
GF=np.array([feat(a) for a in G])
top={i:set() for i in range(len(G))}
CAN={}
for fp in fonts:
    for size in (14,15,16):
        f=ImageFont.truetype(fp,size)
        Rs=[render(c,f) for c in cands]
        CF=np.array([feat(r) for r in Rs]); S=GF@CF.T
        tk=np.argsort(-S,1)[:,:6]
        for i in range(len(G)): top[i].update(tk[i].tolist())
        CAN[(fp,size)]=[canvas(r) for r in Rs]
    print(fp,file=sys.stderr)
shifts=[(dy,dx) for dy in (-1,0,1) for dx in (-1,0,1)]
res=[]
for i in range(len(G)):
    gc,gs=canvas(G[i])
    GS=np.stack([np.roll(np.roll(gc,dy,0),dx,1).ravel() for dy,dx in shifts]); GS=GS-GS.mean(1,keepdims=True); GS/=np.linalg.norm(GS,axis=1,keepdims=True)+1e-6
    best=(-2,'?')
    for ci in top[i]:
        for k in CAN:
            rc,rs=CAN[k][ci]; v=rc.ravel()-rc.mean(); v/=np.linalg.norm(v)+1e-6
            sc=float((GS@v).max())
            # size penalty
            sc-=0.02*(abs(gs[0]-rs[0])+abs(gs[1]-rs[1])) if gs and rs else 0
            if sc>best[0]: best=(sc,cands[ci])
    res.append(best)
json.dump(res,open(os.environ.get('OCROUT','work/ocr_raw.json'),'w',encoding='utf8'),ensure_ascii=False)
