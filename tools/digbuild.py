"""Rebuild cfc.dig: unchanged entries copy original stored bytes, replaced ones are recompressed.
Then write ISO: copy original up to cfc.dig's LBA, append new dig, fix directory record + PVD size."""
import struct,sys,os;sys.path.insert(0,os.path.dirname(__file__))
from dig import entries,DIG
from cc2lz import compress
SEC=0x800
def build_dig(replaced,out):
    """replaced: {entry_index: raw bytes}"""
    E=entries(); src=open(DIG,'rb'); hdr=bytearray(src.read(0x10800))
    fo=open(out,'wb'); fo.write(b'\0'*0x10800); sec=0x10800//SEC
    for e in sorted(E,key=lambda e:e['sec']):
        if e['i'] in replaced:
            raw=replaced[e['i']]
            data=compress(raw) if e['flag'] else raw
            usize=len(raw)
        else:
            src.seek(e['sec']*SEC); data=src.read(e['csize']); usize=e['usize']
        struct.pack_into('<IIII',hdr,e['i']*16,sec,len(data),e['cnt']|(e['flag']<<16),usize)
        fo.write(data); fo.write(b'\0'*((-len(data))%SEC)); sec+=(len(data)+SEC-1)//SEC
    fo.seek(0); fo.write(hdr); fo.close()
def build_iso(src_iso,dig_path,out_iso,eboot=None):
    import pycdlib
    iso=pycdlib.PyCdlib(); iso.open(src_iso)
    rec=iso.get_record(iso_path='/PSP_GAME/USRDIR/cfc.dig'); lba=rec.extent_location()
    iso.close()
    fi=open(src_iso,'rb'); fo=open(out_iso,'wb')
    left=lba*SEC
    while left: b=fi.read(min(left,1<<24)); fo.write(b); left-=len(b)
    dsz=os.path.getsize(dig_path); fd=open(dig_path,'rb')
    while True:
        b=fd.read(1<<24)
        if not b: break
        fo.write(b)
    fo.write(b'\0'*((-dsz)%SEC)); total=fo.tell()//SEC
    # directory record: find in USRDIR directory sectors
    def patch_rec(name,newlba,newsize):
        f=open(out_iso,'r+b')
        f.seek(16*SEC); pvd=bytearray(f.read(SEC))
        struct.pack_into('<I',pvd,80,total); struct.pack_into('>I',pvd,84,total)
        f.seek(16*SEC); f.write(pvd)
        # scan all directory sectors near start for the record
        f.seek(0); head=f.read(64*SEC)
        key=name.encode()
        i=head.find(key)
        while i>=0:
            r=i-33
            if head[r+32]==len(key):
                f.seek(r+2); f.write(struct.pack('<I',newlba)+struct.pack('>I',newlba))
                f.seek(r+10); f.write(struct.pack('<I',newsize)+struct.pack('>I',newsize)); break
            i=head.find(key,i+1)
        else: raise Exception('rec not found')
        f.close()
    fo.close()
    patch_rec('cfc.dig',lba,dsz)
    if eboot:
        f=open(out_iso,'r+b'); iso=pycdlib.PyCdlib(); iso.open(src_iso)
        for p in ('/PSP_GAME/SYSDIR/EBOOT.BIN',):
            r=iso.get_record(iso_path=p); assert len(eboot)<=((r.data_length+SEC-1)//SEC)*SEC
            f.seek(r.extent_location()*SEC); f.write(eboot)
        iso.close(); f.close()
