# Docker Desktop 가상화 비활성화로 실행 실패 (Windows)

## 발생한 오류

```
Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED
```

또는:

```
Hardware assisted virtualization and data execution protection must be enabled in the BIOS.
```

또는 Docker Desktop 시작 시 "Docker Desktop is starting..." 상태에서 무한 대기 후 실패.

## 당시 상황

- Windows 환경에서 Docker Desktop 설치 후 처음 실행하거나 재설치 후 실행 시 발생
- WSL 2 기반 또는 Hyper-V 기반 모드 모두에서 발생 가능
- VDI(가상 데스크탑) 환경에서도 발생

## 확인한 내용

**작업 관리자로 가상화 지원 여부 확인:**

작업 관리자(Ctrl+Shift+Esc) → 성능 탭 → CPU → "가상화: 사용" 여부 확인

**명령 프롬프트에서 WSL 상태 확인:**

```powershell
wsl -l -v
```

**Hyper-V 설치 여부 확인:**

```powershell
Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V
```

## 원인

Docker Desktop은 Windows에서 WSL 2 또는 Hyper-V를 사용해 Linux 컨테이너를 실행함. 아래 중 하나가 충족되지 않으면 실행 불가:

- BIOS에서 Intel VT-x 또는 AMD-V 가상화 기술이 비활성화됨
- Windows 기능에서 "가상 머신 플랫폼" 또는 "Linux용 Windows 하위 시스템" 미설치
- Hyper-V가 설치되어 있지 않거나 부팅 시 Hypervisor가 비활성화됨

## 해결 방법

**방법 1: WSL 2 기반 (권장)**

1. BIOS에서 가상화 활성화 (Intel VT-x 또는 AMD-V)
2. Windows 기능 설치:

```powershell
# 관리자 권한 PowerShell
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
```

3. 재시작 후 WSL 2를 기본값으로 설정:

```powershell
wsl --set-default-version 2
```

**방법 2: Hyper-V 기반**

1. Hyper-V 설치 (Windows Pro/Enterprise 필요):

```powershell
dism.exe /Online /Enable-Feature /All /FeatureName:Microsoft-Hyper-V
```

2. BIOS에서 가상화 활성화
3. Hypervisor 부팅 활성화:

```powershell
bcdedit /set hypervisorlaunchtype auto
```

4. 시스템 재시작

**방법 3: VDI 환경 - 중첩 가상화 활성화**

VDI 관리자에게 중첩 가상화(Nested Virtualization) 활성화 요청 필요.

## 재발 방지

- Windows 업데이트 이후 Hypervisor 설정이 초기화될 수 있으므로, 업데이트 후 재확인
- 기업 환경에서는 BIOS 가상화 설정을 IT 정책으로 기본 활성화
- VDI 환경에서 Docker Desktop을 사용하는 경우 처음부터 중첩 가상화 지원 여부를 확인

## 참고

- https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/
- https://learn.microsoft.com/windows/wsl/install
