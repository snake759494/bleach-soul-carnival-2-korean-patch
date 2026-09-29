#!/bin/bash
# usage: boottest.sh iso seconds   — waits for the shared PPSSPP lock (D:/psp/ppsspp_win/LOCK.txt)
LOCK=/d/psp/ppsspp_win/LOCK.txt
while [ -f "$LOCK" ] && ! grep -q 블리치 "$LOCK"; do sleep 20; done
echo 블리치-소울카니발2 > "$LOCK"
taskkill //IM PPSSPPWindows64.exe //F >/dev/null 2>&1; sleep 1
cd /d/psp/ppsspp_win && (./PPSSPPWindows64.exe "$(cygpath -w "$1")" &)
sleep ${2:-30}
cd /c/Users/Jay/Downloads/psp/블리치-소울카니발2
python tools/shot.py boot
