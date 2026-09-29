"""cfc.dig archive: header 16B zero, then 16B entries (sector, stored size, u16 count, u16 flag(1=compressed), raw size)."""
import struct
DIG='work/iso/PSP_GAME/USRDIR/cfc.dig'
def entries(path=DIG):
    h=open(path,'rb').read(0x10800); out=[]
    for i in range(1,0x10800//16):
        a,b,c,d=struct.unpack_from('<IIII',h,i*16)
        if a==0 and b==0 and c==0: continue
        out.append(dict(i=i,sec=a,csize=b,cnt=c&0xffff,flag=c>>16,usize=d))
    return out
