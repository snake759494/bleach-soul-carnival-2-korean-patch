"""Preview auto-detected text boxes for flagged images -> work/imgprev/<key>.png and work/imgprev/list.json"""
import sys,json,os;sys.path.insert(0,'tools')
from PIL import Image,ImageDraw
import imgloc
SKIP_A0={8,9,10,11,12,13,14,15,16,352,349,350,351,72,73,74,75,76,77,78,79,80,81,82,83,84,194,388,389,390,403,404,405,406,407,408,1824,206,208,272}
SKIP_A1={2889,2926,3138,3140}
SKIP_B0={33,34}
os.makedirs('work/imgprev',exist_ok=True)
L=[]
import os as _o
TAGS=[('a0','a',SKIP_A0),('a1','a',SKIP_A1),('b0','b',SKIP_B0)] if not _o.environ.get('ONLY') else [(t,t[0],set()) for t in _o.environ['ONLY'].split(',')]
for tag,sheet,skip in TAGS:
    items=json.load(open('work/sheets_%s/items.json'%sheet))
    for x in json.load(open('work/imgreview/%s.json'%tag,encoding='utf8')):
        if x['idx'] in skip: continue
        it=items[x['idx']]; key='%s%d'%(sheet,x['idx'])
        im=Image.open('work/gim/%s.png'%it['hash']).convert('RGBA')
        boxes=imgloc.regions(im)
        s=max(1,min(4,900//max(im.size)))
        bg=Image.new('RGBA',im.size,(40,40,90,255)); bg.alpha_composite(im); bg=bg.resize((im.width*s,im.height*s),Image.NEAREST)
        dr=ImageDraw.Draw(bg)
        for k,(x0,y0,x1,y1) in enumerate(boxes):
            dr.rectangle([x0*s,y0*s,x1*s-1,y1*s-1],outline=(255,0,0)); dr.text((x0*s+1,y0*s+1),str(k),fill=(255,255,0))
        bg.save('work/imgprev/%s.png'%key)
        L.append(dict(key=key,file=it['file'],off=it['off'],page=it['page'],w=it['w'],h=it['h'],hash=it['hash'],ja=x['ja'],ko=x.get('ko'),boxes=[[int(v) for v in b] for b in boxes]))
json.dump(L,open(_o.environ.get('LISTOUT','work/imgprev/list.json'),'w',encoding='utf8'),ensure_ascii=False,indent=0)
print(len(L))
