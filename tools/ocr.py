"""Recover glyph-index -> character table by template matching the game's font atlas."""
import sys,json,numpy as np;sys.path.insert(0,'tools')
from PIL import Image,ImageDraw,ImageFont
from gim import *
from member import members
d=open('work/dig/0002.bin','rb').read(); M=members(d)
g=d[M[2]['off']:M[2]['off']+M[2]['size']]
P=pages(g); pal=palette(g,P[0])[:,3].astype(np.float32)/255
glyphs=[]
for e in P:
    a=pal[page_pixels(g,e)]
    for r in range(a.shape[0]//16):
        for c in range(16): glyphs.append(a[r*16:r*16+16,c*16:c*16+16])
G=np.array(glyphs); np.save('work/glyphs.npy',G)
# candidates
cands=[chr(c) for c in range(0x21,0x7f)]
for hi in range(0x81,0xa0):
    for lo in range(0x40,0xfd):
        try: cands.append(bytes([hi,lo]).decode('cp932'))
        except: pass
for hi in range(0xe0,0xeb):
    for lo in range(0x40,0xfd):
        try: cands.append(bytes([hi,lo]).decode('cp932'))
        except: pass
cands=list(dict.fromkeys(c for c in cands if len(c)==1))
fonts=[('C:/Windows/Fonts/msgothic.ttc',0),('C:/Windows/Fonts/meiryo.ttc',0),('C:/Windows/Fonts/YuGothM.ttc',0),('C:/Windows/Fonts/BIZ-UDGothicR.ttc',0)]
def render(ch,f):
    im=Image.new('L',(24,24)); ImageDraw.Draw(im).text((4,4),ch,font=f,fill=255); return np.asarray(im,np.float32)/255
def feat(a,n=12):
    ys,xs=np.nonzero(a>0.25)
    if len(ys)==0: return np.zeros(n*n+4,np.float32)
    y0,y1,x0,x1=ys.min(),ys.max()+1,xs.min(),xs.max()+1
    im=Image.fromarray((a[y0:y1,x0:x1]*255).astype(np.uint8)).resize((n,n),Image.BILINEAR)
    v=np.asarray(im,np.float32).ravel()/255; v=v-v.mean(); v/= (np.linalg.norm(v)+1e-6)
    # size features (scaled): height,width,center
    return np.concatenate([v,np.array([(y1-y0)/16,(x1-x0)/16,(y0+y1)/32,(x0+x1)/32],np.float32)*0.6])
GF=np.array([feat(a) for a in G])
best=[(-9,'?')]*len(G)
for fp,idx in fonts:
    for size in (14,15,16):
        f=ImageFont.truetype(fp,size,index=idx)
        R=[render(c,f) for c in cands]
        CF=np.array([feat(r) for r in R])
        S=GF@CF.T
        am=S.argmax(1)
        for i in range(len(G)):
            s=S[i,am[i]]
            if s>best[i][0]: best[i]=(float(s),cands[am[i]])
        print(fp,size,file=sys.stderr)
json.dump(best,open('work/ocr_raw.json','w',encoding='utf8'),ensure_ascii=False)
