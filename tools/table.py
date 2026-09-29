import json
_b=json.load(open('work/ocr_raw.json',encoding='utf8'))
TAB=[x[1] for x in _b]
for i in range(0x5e): TAB[i]=chr(0x20+i) if i<0x3f else chr(0x21+i)  # '`'..'~' shifted down by one
TAB[0x0C]='.'; TAB[0x0D]='-'; TAB[0x0E]='_'
try:
    for k,v in json.load(open('translation/ocr_fix.json',encoding='utf8')).items(): TAB[int(k,16)]=v
except FileNotFoundError: pass
def dec(seq):
    s=''
    for c in seq:
        if c==0x8010: s+='\n'
        elif c>=0x8000: s+='{%04X}'%c
        elif c<len(TAB): s+=TAB[c]
        else: s+='{%04X}'%c
    return s
