# 기술 메모

## 준비
1. `python tools/extract_iso.py 원본.iso work/iso`
2. `tools/bin/eboot_decrypt.exe work/iso/PSP_GAME/SYSDIR/EBOOT.BIN work/eboot_plain.bin` (분석용. 패치에는 EBOOT 변경 없음)
3. `python tools/unpack_all.py` — cfc.dig 전체 엔트리를 `work/dig/NNNN.bin`으로 해제
4. `python tools/collect.py` → `work/blocks.json`(메시지 표), `python tools/mkdb.py` → 번역 DB

## cfc.dig (`tools/dig.py`, `tools/digbuild.py`)
- 헤더 0x10800바이트: 16바이트 엔트리 `(섹터, 저장 크기, u16 멤버 수 | u16 압축 플래그<<16, 원본 크기)`. 섹터 = 0x800바이트.
- 압축은 나루티밋 임팩트와 같은 9비트 문맥 LZ(`tools/cc2lz.py`). 게임이 위치표를 초기화하지 않으므로 인코더는 기록되지 않은 슬롯을 쓰지 않는다.
- 해제 루프(EBOOT 0x2f80)는 출력 크기가 아니라 입력 csize를 다 읽을 때까지 토큰을 푼다. 스트림 끝에 여분 바이트가 있으면 출력 버퍼 뒤를 덮어써 로딩·영상 재생 중 멈춤·크래시가 난다. 압축본은 ⌈9N/8⌉바이트로 딱 끝내야 한다.
- ISO의 마지막 파일이므로 그 자리에서 교체·확장하고 디렉터리 레코드와 PVD 볼륨 크기만 고친다.

## 멤버 컨테이너 (`tools/member.py`)
24바이트 엔트리 `(id, 크기, 오프셋, 0, 타입, 0)`, 헤더 크기 = 첫 오프셋.

## 텍스트
- 문자열은 u16 **글리프 번호**: 0x8000 끝, 0x8001 대사 줄바꿈, 0x8010 줄바꿈, 0x8008/0x800F·0x800A/0x8007 색, 0x8029 대사 끝, 0x81xx 화자, 0x10xx 아이콘 폰트.
- 메시지 표(`tools/msgblk.py`): A형 `u32 off[n]`(off[0]=4n), B형 `u32 n, u32 off[n]`(off[0]=4+4n). 오프셋 기준 = 표(또는 개수) 시작. 문자열 풀은 표 뒤에 빈틈 없이 붙어 있어 풀 안에서 자유롭게 재배치(중복 공유)한다.
- 풀 크기는 늘릴 수 없다. 엔트리 끝에 덧붙이면 스테이지 로딩이 멈춘다. `tools/pressure.py`·`tools/targets.py`로 풀별 초과량을 긴 문장에 나눠 목표 길이를 정하고 번역을 다듬었다.
- 문자표는 원본에 없어서 폰트 아틀라스를 OCR로 복원했다(`tools/ocr2.py`, 보정 `translation/ocr_fix.json`). 영문 소문자는 `_` 글리프가 없어 한 칸 당겨져 있다.

## 폰트 (dig 0002)
- 멤버 2: GIM, 8bpp 스위즐 256×256 페이지 7장 + 256×32, 16px 셀(페이지당 256자). 팔레트 인덱스 0~128 = 흰색 알파 255→0.
- 멤버 4: 글리프별 폭(전각 15). 한글은 나눔스퀘어네오 Regular 16px, 기호는 원본 글리프를 재사용.
- 멤버 3: 아이콘 폰트(0x1000+). 버튼·희귀 한자(瀞·殛 등)·배지. 희귀 한자 코드는 번역문에서 한글로 풀어 쓰고, 배지 破·仮·死·虚는 파·가·사·호로 다시 그림(`tools/badge.py`).

## 테스트
`bash tools/boottest.sh ISO 30`, `python tools/shot.py 이름 버튼...` (PPSSPP 원격 디버거).
