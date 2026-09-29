"""hold right, tap cross/circle periodically: python tools/walk.py seconds shotname"""
import sys,time;sys.path.insert(0,'tools')
from ppsspp_rpc import Debugger
S='C:/Users/Jay/AppData/Local/Temp/claude/C--Users-Jay-Downloads-psp----------2/5f9d0a85-04fe-4aaf-af82-cb495733d9f5/scratchpad/'
d=Debugger(); t=time.time(); k=0
while time.time()-t<float(sys.argv[1]):
    d.call('input.buttons.send',buttons={'right':True})
    b=['cross','circle','square'][k%3]; k+=1
    d.call('input.buttons.press',button=b,duration=3); time.sleep(0.4)
d.call('input.buttons.send',buttons={'right':False})
d.frame(S+sys.argv[2]+'.png')
