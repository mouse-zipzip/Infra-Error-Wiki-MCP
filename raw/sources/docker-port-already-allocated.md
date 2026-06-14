# Docker 컨테이너 실행 시 포트 이미 사용 중 오류

## 발생한 오류

```
Bind for 0.0.0.0:8080 failed: port is already allocated
```

또는:

```
listen tcp 0.0.0.0:8080: bind: address is already in use
```

`docker run` 또는 `docker-compose up` 실행 시 컨테이너가 시작되지 않고 위 오류가 출력됨.

## 당시 상황

- `docker run -p 8080:8080 ...` 또는 `docker-compose up` 실행 중 발생
- 이전에 실행한 컨테이너가 정상적으로 종료되지 않았거나, 호스트의 다른 프로세스(Spring Boot, Node.js 등)가 동일한 포트를 점유 중인 경우 발생

## 확인한 내용

**Windows - 해당 포트를 사용 중인 PID 확인:**

```powershell
netstat -aon | find /i "listening" | find "8080"
# 또는 리소스 모니터(resmon.exe)의 네트워크 탭에서 확인
```

**Mac/Linux - 해당 포트를 사용 중인 프로세스 확인:**

```bash
lsof -i :8080
# 또는
ss -tlnp | grep 8080
```

**실행 중인 Docker 컨테이너 목록 확인:**

```bash
docker ps -a
```

## 원인

호스트의 특정 포트는 동시에 하나의 프로세스만 bind 할 수 있음. 아래 중 하나에 해당:

- 이전에 실행한 Docker 컨테이너가 `docker stop` 없이 종료되어 포트를 계속 점유
- 호스트에서 실행 중인 다른 프로세스(Spring Boot, Nginx, 개발 서버 등)가 같은 포트 사용
- `docker-compose down` 없이 프로세스를 종료하여 컨테이너가 남아 있음

## 해결 방법

**방법 1: 기존 컨테이너 중지**

```bash
docker ps -a
docker stop <container_id>
# 또는 컨테이너 삭제
docker rm <container_id>
```

**방법 2: 포트 점유 프로세스 종료 (Windows)**

```powershell
netstat -aon | find /i "listening" | find "8080"
# PID 확인 후
taskkill /PID <PID> /F
```

**방법 3: 포트 점유 프로세스 종료 (Mac/Linux)**

```bash
lsof -i :8080
kill -9 <PID>
```

**방법 4: 다른 포트로 변경**

```bash
docker run -p 8081:8080 ...
```

또는 `docker-compose.yml`에서 ports 항목 수정.

## 재발 방지

- 컨테이너 종료 시 `docker-compose down` 또는 `docker stop` + `docker rm`을 사용하는 습관을 들임
- 개발 환경에서 포트 사용 규칙을 팀 내에서 정의하고 공유함 (예: 8080 = 메인 앱, 5432 = DB 전용)
- `docker-compose.yml`에서 포트 번호를 환경 변수로 관리하여 충돌 시 쉽게 변경 가능하도록 함

## 참고

- https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/
