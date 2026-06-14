# Docker 볼륨 마운트 시 런타임 오류 또는 파일 접근 실패

## 대표 증상

- `Error response from daemon: Mounts denied:`
- `The path is not shared from the host and is not known to Docker.`
- `Permission denied`
- `open /app/data/file.txt: no such file or directory`

---

## 원인

Docker Desktop은 허용된 host 경로만 container에 공유하므로, 공유 목록에 없는 경로나 권한이 맞지 않는 경로를 mount하면 daemon 또는 container 내부 파일 접근 오류가 발생합니다.

---

## 원인 유형

### Docker 볼륨 마운트 시 런타임 오류 또는 파일 접근 실패

증상:
- `Error response from daemon: Mounts denied:`
- `Permission denied`

원인:
Docker Desktop은 보안상 기본적으로 허용된 경로만 컨테이너에 공유함. 홈 디렉토리 하위는 기본 공유 대상이지만, 그 외 경로(예: `/data`, `D:\projects`)는 명시적으로 파일 공유를 등록해야 함. Windows의 경우 Hyper-V 기반 Docker에서 드라이브 단위로 공유를 설정해야 함.

해결:
- `방법 1: Docker Desktop 파일 공유 설정에 경로 추가`
- `방법 2: 홈 디렉토리 하위로 프로젝트 이동`
- `방법 3: Docker named volume 사용 (호스트 경로 마운트 대신)`

요약:
- 원본: `raw/sources/docker-volume-mount-runtime-error.md`
- 상황: `-v /host/path:/container/path` 옵션으로 볼륨을 마운트하여 컨테이너를 실행할 때 발생
- 해결 요약: 방법 1: Docker Desktop 파일 공유 설정에 경로 추가

---

## 검색 태그

docker, volume, mount, file-sharing, container, desktop, port

---
