# Docker 볼륨 마운트 시 런타임 오류 또는 파일 접근 실패

## 발생한 오류

컨테이너 실행 시 또는 실행 중에 마운트된 볼륨에 접근할 때 오류 발생:

```
Error response from daemon: Mounts denied:
The path /Users/myuser/projects is not shared from the host and is not known to Docker.
```

또는 컨테이너 내부에서 파일을 읽거나 쓸 때:

```
Permission denied
open /app/data/file.txt: no such file or directory
```

## 당시 상황

- `-v /host/path:/container/path` 옵션으로 볼륨을 마운트하여 컨테이너를 실행할 때 발생
- 프로젝트 디렉토리가 홈 디렉토리(`/home/<user>` 또는 `C:\Users\<user>`) 외부에 있는 경우
- Docker Desktop의 파일 공유 설정에 해당 경로가 등록되어 있지 않은 경우

## 확인한 내용

Docker Desktop → Settings → Resources → File sharing 탭에서 마운트하려는 호스트 경로가 공유 목록에 포함되어 있는지 확인:

- **Mac/Linux:** Settings > Resources > File sharing
- **Windows:** Settings > Shared Folders

마운트 경로가 목록에 없으면 Docker가 해당 경로에 접근할 수 없음.

```bash
# 컨테이너 내부에서 마운트된 디렉토리 확인
docker exec -it <container_id> ls -la /app/data
```

## 원인

Docker Desktop은 보안상 기본적으로 허용된 경로만 컨테이너에 공유함. 홈 디렉토리 하위는 기본 공유 대상이지만, 그 외 경로(예: `/data`, `D:\projects`)는 명시적으로 파일 공유를 등록해야 함.

Windows의 경우 Hyper-V 기반 Docker에서 드라이브 단위로 공유를 설정해야 함.

## 해결 방법

**방법 1: Docker Desktop 파일 공유 설정에 경로 추가**

1. Docker Desktop → Settings (톱니바퀴 아이콘)
2. Resources → File sharing
3. `+` 버튼을 눌러 마운트하려는 호스트 경로를 추가
4. Apply & Restart

**방법 2: 홈 디렉토리 하위로 프로젝트 이동**

프로젝트 디렉토리를 기본 공유 경로인 홈 디렉토리 내로 이동:

```bash
mv /data/myproject ~/projects/myproject
```

**방법 3: Docker named volume 사용 (호스트 경로 마운트 대신)**

```bash
docker volume create mydata
docker run -v mydata:/app/data ...
```

## 재발 방지

- 개발 프로젝트는 홈 디렉토리 하위에서 관리하는 것을 원칙으로 함
- 팀 환경 설정 가이드에 Docker 파일 공유 설정 경로를 문서화함
- `docker-compose.yml`의 volumes 설정은 상대 경로를 사용하여 이식성을 높임

## 참고

- https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/
