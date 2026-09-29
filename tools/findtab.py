import glob,sys
def isj(c): return 0x3040<=c<=0x30ff or 0x4e00<=c<=0x9fff or 0xff00<=c<=0xffef or 0x3000<=c<0x3040
def kana(c): return 0x3041<=c<=0x30fa
paths=sys.argv[1:] or sorted(glob.glob('work/dig/*.bin'))+['work/eboot_plain.bin']
for p in paths:
    d=open(p,'rb').read()
    for al in (0,1):
        run=[];st=0
        for i in range(al,len(d)-1,2):
            c=d[i]|d[i+1]<<8
            if isj(c) or c in (0x20,0x0a) or 0x21<=c<0x7f:
                if not run: st=i
                run.append(c)
            else:
                if len(run)>=6 and sum(map(kana,run))>=len(run)*0.3 and len(set(run))>len(run)*0.4:
                    print(p,hex(st),len(run),''.join(map(chr,run[:30])).replace('\n','/'))
                run=[]
