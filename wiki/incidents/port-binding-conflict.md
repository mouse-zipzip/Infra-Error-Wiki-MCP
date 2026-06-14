# Port Binding Conflict

## 대표 증상

- `port is already allocated`
- `address already in use`
- `bind failed`
- `EADDRINUSE`
- `Bind for 0.0.0.0:8080 failed: port is already allocated`

---

## 원인

Host의 특정 port는 동시에 하나의 process만 bind할 수 없습니다.

---

## 원인 유형

### Docker 컨테이너 실행 시 포트 이미 사용 중 오류

증상:
- `Bind for 0.0.0.0:8080 failed: port is already allocated`

원인:
- 이전에 실행한 Docker 컨테이너가 `docker stop` 없이 종료되어 포트를 계속 점유
- `호스트에서 실행 중인 다른 프로세스(Spring Boot, Nginx, 개발 서버 등)가 같은 포트 사용`
- `docker-compose down` 없이 프로세스를 종료하여 컨테이너가 남아 있음

해결:
- `방법 1: 기존 컨테이너 중지`
- `방법 2: 포트 점유 프로세스 종료 (Windows)`
- `방법 3: 포트 점유 프로세스 종료 (Mac/Linux)`
- `방법 4: 다른 포트로 변경`

요약:
- 원본: `raw/sources/docker-port-already-allocated.md`
- 상황: `docker run -p 8080:8080 ...` 또는 `docker-compose up` 실행 중 발생
- 해결 요약: 방법 1: 기존 컨테이너 중지

---

## 검색 태그

port, bind, networking, docker, nginx, spring-boot, desktop, container

---
