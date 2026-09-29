#!/bin/bash
# end a test: close PPSSPP and release the shared lock
taskkill //IM PPSSPPWindows64.exe //F >/dev/null 2>&1
grep -q 블리치 /d/psp/ppsspp_win/LOCK.txt 2>/dev/null && rm -f /d/psp/ppsspp_win/LOCK.txt
true
