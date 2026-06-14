# Docker Desktop 시작/표시 오류

## 대표 증상

- `Docker Desktop - Access Denied`
- `Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED`
- `Docker Desktop UI 녹색/왜곡/아티팩트`
- `Docker Desktop을 시작하려고 할 때 위 팝업이 나타나며 앱이 실행되지 않음.`

- `Docker Desktop 앱을 열었을 때 UI가 아래 중 하나로 나타남`
- 화면 전체가 녹색으로 덮임
- UI 요소가 왜곡되거나 깨져서 보임
- `잔상(artifact)이 남거나 렌더링이 제대로 되지 않음`

---

## 원인

docker-users 그룹 미포함, Windows Hyper-V/WSL2 비활성화, BIOS 가상화 비활성화, GPU 하드웨어 가속 충돌 등

---

## 원인 유형

### Docker Desktop 시작 시 Access Denied 오류

증상:
- `Docker Desktop - Access Denied`
- `Docker Desktop을 시작하려고 할 때 위 팝업이 나타나며 앱이 실행되지 않음.`

원인:
Docker Desktop은 Windows에서 Docker 리소스에 접근하기 위해 `docker-users` 라는 로컬 그룹을 사용함. 이 그룹에 속하지 않은 사용자는 Docker Desktop을 실행할 권한이 없어 "Access Denied" 오류가 발생함.

확인:
1. 현재 사용자가 docker-users 그룹에 속해 있는지 확인
2. 또는 컴퓨터 관리 → 로컬 사용자 및 그룹 → 그룹 → docker-users → 구성원 목록 확인.

해결:
- `방법 1: GUI (컴퓨터 관리)`
- `방법 2: 명령 프롬프트 (관리자 권한)`
- 로그아웃 후 재로그인

요약:
- 원본: `raw/sources/docker-desktop-access-denied-windows.md`
- 상황: Windows에서 Docker Desktop을 설치한 후 처음 실행하거나, 새 사용자 계정으로 로그인하여 실행할 때 발생
- 해결 요약: 방법 1: GUI (컴퓨터 관리)

---

### Docker Desktop UI가 녹색/왜곡/아티팩트로 표시됨

증상:
- `Docker Desktop 앱을 열었을 때 UI가 아래 중 하나로 나타남`
- 화면 전체가 녹색으로 덮임
- UI 요소가 왜곡되거나 깨져서 보임
- `잔상(artifact)이 남거나 렌더링이 제대로 되지 않음`

원인:
Docker Desktop의 UI 렌더링에 사용되는 하드웨어 가속(GPU)이 특정 GPU 드라이버 또는 환경과 호환되지 않아 렌더링 오류 발생.

확인:
1. settings-store.json 파일 위치
2. **Mac:** ~/Library/Group Containers/group.com.docker/settings-store.json
3. **Windows:** C:\Users\<사용자명>\AppData\Roaming\Docker\settings-store.json
4. **Linux:** ~/.docker/desktop/settings-store.json

해결:
- `Docker Desktop 완전 종료`
- `settings-store.json` 파일 열기
- 다음 항목 추가 또는 수정
- `Docker Desktop 재시작`

요약:
- 원본: `raw/sources/docker-desktop-ui-visual-artifacts.md`
- 상황: Docker Desktop 설치 또는 업데이트 후 앱을 처음 실행할 때 발생
- 해결 요약: Docker Desktop 완전 종료

---

### Docker Desktop 가상화 비활성화로 실행 실패

증상:
- `Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED`

원인:
- `BIOS에서 Intel VT-x 또는 AMD-V 가상화 기술이 비활성화됨`
- `Windows 기능에서 "가상 머신 플랫폼" 또는 "Linux용 Windows 하위 시스템" 미설치`
- `Hyper-V가 설치되어 있지 않거나 부팅 시 Hypervisor가 비활성화됨`

해결:
- `방법 1: WSL 2 기반 (권장)`
- `방법 2: Hyper-V 기반`
- `방법 3: VDI 환경 - 중첩 가상화 활성화`

요약:
- 원본: `raw/sources/docker-desktop-virtualization-disabled.md`
- 상황: Windows 환경에서 Docker Desktop 설치 후 처음 실행하거나 재설치 후 실행 시 발생
- 해결 요약: 방법 1: WSL 2 기반 (권장)

---

## 검색 태그

docker, desktop, windows, hyper-v, virtualization, access-denied, port

---
