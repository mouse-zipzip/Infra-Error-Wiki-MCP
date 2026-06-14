# Docker Desktop 시작 시 Access Denied 오류 (Windows)

## 발생한 오류

```
Docker Desktop - Access Denied
```

Docker Desktop을 시작하려고 할 때 위 팝업이 나타나며 앱이 실행되지 않음.

## 당시 상황

- Windows에서 Docker Desktop을 설치한 후 처음 실행하거나, 새 사용자 계정으로 로그인하여 실행할 때 발생
- 관리자가 Docker Desktop을 설치했으나 현재 로그인 사용자가 `docker-users` 그룹에 속하지 않을 때 발생

## 확인한 내용

현재 사용자가 `docker-users` 그룹에 속해 있는지 확인:

```powershell
net localgroup docker-users
```

또는 컴퓨터 관리 → 로컬 사용자 및 그룹 → 그룹 → `docker-users` → 구성원 목록 확인.

## 원인

Docker Desktop은 Windows에서 Docker 리소스에 접근하기 위해 `docker-users` 라는 로컬 그룹을 사용함. 이 그룹에 속하지 않은 사용자는 Docker Desktop을 실행할 권한이 없어 "Access Denied" 오류가 발생함.

## 해결 방법

관리자 권한으로 현재 사용자를 `docker-users` 그룹에 추가:

**방법 1: GUI (컴퓨터 관리)**

1. 시작 메뉴 → "컴퓨터 관리"를 관리자로 실행
2. 로컬 사용자 및 그룹 → 그룹 → `docker-users` 더블 클릭
3. 추가 버튼 → 현재 사용자 계정명 입력 → 확인
4. 로그아웃 후 다시 로그인

**방법 2: 명령 프롬프트 (관리자 권한)**

```powershell
net localgroup docker-users <사용자명> /add
```

또는:

```powershell
Add-LocalGroupMember -Group "docker-users" -Member "<사용자명>"
```

그룹 추가 후 반드시 **로그아웃 후 재로그인**해야 적용됨.

## 재발 방지

- Docker Desktop 설치 후 사용할 모든 사용자를 `docker-users` 그룹에 추가하는 것을 설치 체크리스트에 포함
- 기업 환경에서는 Active Directory 그룹 정책으로 `docker-users` 그룹 멤버십을 자동 관리

## 참고

- https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/
