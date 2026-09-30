"""UTF-8 string tables in dig 0012 (save-data texts): u16 n, u16 hdr, then n x (u16 off, u16 len), strings at off."""
import struct
def parse(b):
    n=struct.unpack_from('<H',b,0)[0]
    ents=[struct.unpack_from('<HH',b,4+4*i) for i in range(n)]
    return [b[o:o+l].decode('utf8') for o,l in ents]
def build(orig,strs):
    n=len(strs); hdr=4+4*n; out=bytearray(orig[:4]); body=bytearray(); ents=[]
    for s in strs:
        e=s.encode('utf8'); ents.append((hdr+len(body),len(e))); body+=e
    for o,l in ents: out+=struct.pack('<HH',o,l)
    out+=body
    if len(out)>len(orig): raise Exception('utf8 table too long %d>%d'%(len(out),len(orig)))
    return bytes(out)+bytes(len(orig)-len(out))
