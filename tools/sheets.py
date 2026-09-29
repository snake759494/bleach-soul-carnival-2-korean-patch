"""Contact sheets of unique GIM pages. usage: sheets.py outdir minfile maxfile [sample_every]"""
import json,sys,os
from PIL import Image,ImageDraw
X=json.load(open('work/gim_index.json'))
out,lo,hi=sys.argv[1],int(sys.argv[2]),int(sys.argv[3]); step=int(sys.argv[4]) if len(sys.argv)>4 else 1
first={}
for x in X: first.setdefault(x['hash'],x)
MINW=int(os.environ.get('MINW','0')); MINH=int(os.environ.get('MINH','0'))
U=[x for x in first.values() if lo<=x['file']<=hi and x['w']*x['h']>=24*24 and x['w']>=MINW and x['h']>=MINH]
U.sort(key=lambda x:(x['file'],x['off'],x['page'])); U=U[::step]
os.makedirs(out,exist_ok=True)
T=150; C=8; R=6
meta=[]
for s in range(0,len(U),C*R):
    sh=Image.new('RGB',(C*T,R*(T+14)),(70,70,110)); dr=ImageDraw.Draw(sh)
    for k,x in enumerate(U[s:s+C*R]):
        im=Image.open('work/gim/%s.png'%x['hash']).convert('RGBA'); im.thumbnail((T-4,T-4))
        bg=Image.new('RGBA',im.size,(30,30,30,255)); bg.alpha_composite(im)
        cx=(k%C)*T; cy=(k//C)*(T+14); sh.paste(bg,(cx+2,cy+2))
        dr.text((cx+2,cy+T),'%d #%d %dx%d'%(s+k,x['file'],x['w'],x['h']),fill=(255,255,0))
    sh.save('%s/sheet%03d.png'%(out,s//(C*R)))
json.dump(U,open(out+'/items.json','w'))
print(len(U),'items',(len(U)+47)//48,'sheets')
