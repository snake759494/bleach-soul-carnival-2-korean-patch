import struct, sys, collections
def parse(path):
    f=open(path,'rb'); hdr=f.read(0x100000)
    ents=[]; first=None
    for i in range(0,len(hdr),16):
        o,s,fl,u=struct.unpack_from('<4I',hdr,i)
        if first is not None and i>=first*0x800: break
        ents.append((o,s,fl,u))
        if o and (first is None or o<first): first=o
    return ents
if __name__=='__main__':
    e=parse(sys.argv[1]); print(len(e))
    print(collections.Counter(x[2] for x in e))
    print(sum(1 for x in e if x[1]!=x[3]))
    for i,x in enumerate(e[:5]): print(i,x)
