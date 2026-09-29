import sys,os; sys.path.insert(0,'tools')
from dig import entries,DIG
from cc2lz import decompress
from multiprocessing import Pool
os.makedirs('work/dig',exist_ok=True)
def job(e):
    p='work/dig/%04d.bin'%e['i']
    if os.path.exists(p): return
    f=open(DIG,'rb'); f.seek(e['sec']*0x800); d=f.read(e['csize'])
    if e['flag']: d=decompress(d,e['usize'])
    open(p,'wb').write(d)
if __name__=='__main__':
    with Pool(4) as p: p.map(job,entries(),chunksize=4)
    print('done')
