"""Translators copied English words from the old (shifted) decode; replace them with the corrected spelling."""
import json,glob,re
old=json.load(open('work/unique_ja_old.json',encoding='utf8'))
new=json.load(open('translation/unique_ja.json',encoding='utf8'))
n=0
for p in sorted(glob.glob('translation/out/b*.json')):
    out=json.load(open(p,encoding='utf8')); ch=False
    for k,ko in out.items():
        i=int(k); o=old[i]; w=new[i]
        if o==w: continue
        # ascii words that changed
        for m in re.finditer(r"[ -~]+",o):
            a=m.group(); b=w[m.start():m.end()]
            a2=a.strip(); b2=b.strip()
            if a2 and a2!=b2 and a2 in ko and len(a2)>=2:
                ko=ko.replace(a2,b2); ch=True; n+=1
        out[k]=ko
    if ch: json.dump(out,open(p,'w',encoding='utf8'),ensure_ascii=False,indent=0)
print('fixed',n)
