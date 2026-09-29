"""Capture a PPSSPP GE frame dump and list texture draws."""
import sys,struct,base64,zstandard;sys.path.insert(0,'tools')
def capture(path):
    from ppsspp_rpc import Debugger
    d=Debugger(); r=d.call('gpu.record.dump'); open(path,'wb').write(base64.b64decode(r['uri'].split(',',1)[1]))
def parse(path):
    b=open(path,'rb').read(); assert b[:8]==b'PPSSPPGE'
    ver=struct.unpack_from('<I',b,8)[0]; p=0x18
    ncmd,pbsz=struct.unpack_from('<II',b,p); p+=8
    csz=struct.unpack_from('<I',b,p)[0]; p+=4
    dz=zstandard.ZstdDecompressor()
    cmds=dz.decompress(b[p:p+csz],max_output_size=ncmd*9); p+=csz
    psz=struct.unpack_from('<I',b,p)[0]; p+=4
    pb=dz.decompress(b[p:p+psz],max_output_size=pbsz)
    C=[struct.unpack_from('<BII',cmds,i*9) for i in range(ncmd)]
    return C,pb
if __name__=='__main__':
    if sys.argv[1]=='cap': capture(sys.argv[2])
    C,pb=parse(sys.argv[2])
    from collections import Counter
    print(Counter(c[0] for c in C))
