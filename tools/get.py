import sys,os;sys.path.insert(0,os.path.dirname(__file__));import arc,cc2lz
ARCS={'0000':'work/0000_dec.bin','0006':'work/0006_dec.bin','0010':'work/iso/PSP_GAME/USRDIR/0010.BIN'}
_c={}
def get(name,idx):
    if name not in _c: _c[name]=arc.parse(ARCS[name])
    o,s,f,u=_c[name][idx]
    with open(ARCS[name],'rb') as fh: fh.seek(o*0x800); src=fh.read(s)
    return cc2lz.decompress(src,u) if f>>16 else src
