# Docker Private Registry TLS Configuration Failure

## 대표 증상

- `malformed HTTP response "\x15\x03\x01..."`
- `private registry pull/push failure`
- `Docker registry TLS handshake mismatch`
- `Error response from daemon: Get http://192.168.203.139:5858/v2/: malformed HTTP response "\x15\x03\x01\x00\x02\x02"`
- `private registry에서 이미지를 pull하거나 push할 때 위와 같은 응답 파싱 오류가 발생하며 연결 실패.`

- `Error response from daemon: Get "https://192.168.203.139:5858/v2/": http: server gave HTTP response to HTTPS client`

---

## 원인

Docker client와 registry server가 기대하는 HTTP/HTTPS 프로토콜 또는 인증서 신뢰 설정이 일치하지 않습니다.

---

## 원인 유형

### Docker private registry 연결 시 TLS 인증서 오류

증상:
- `Error response from daemon: Get http://192.168.203.139:5858/v2/: malformed HTTP response "\x15\x03\x01\x00\x02\x02"`
- `private registry에서 이미지를 pull하거나 push할 때 위와 같은 응답 파싱 오류가 발생하며 연결 실패.`

원인:
- `Docker 데몬이 HTTP로 요청했으나 서버가 TLS를 강제함`
- `self-signed 인증서를 사용하는 registry에 대한 CA 인증서가 Docker에 등록되어 있지 않음`
- `Docker가 클라이언트 인증서를 서버에 전달하지 않음`

해결:
- `방법 1: self-signed CA 인증서를 Docker에 등록 (HTTPS 유지)`
- `방법 2: insecure registry로 등록 (개발/테스트 환경)`
- `방법 3: registry를 올바른 TLS 인증서로 재구성`

요약:
- 원본: `raw/sources/docker-certificate-config-error.md`
- 상황: 사내 또는 로컬에서 운영하는 private Docker registry에 접근할 때 발생
- 해결 요약: 방법 1: self-signed CA 인증서를 Docker에 등록 (HTTPS 유지)

---

### Docker private registry push 실패 기록

증상:
- `Error response from daemon: Get "https://192.168.203.139:5858/v2/": http: server gave HTTP response to HTTPS client`

원인:
registry는 HTTP로 열려 있었는데 Docker client가 기본적으로 HTTPS registry처럼 접근하려고 해서 문제가 난 것 같다.

해결:
- Docker Desktop Engine 설정에 `insecure-registries`로 `192.168.203.139:5858`을 등록했다.
- `설정 저장 후 Docker Desktop을 재시작했다.`
- `개발용 HTTP registry이므로 Docker client가 해당 registry에 HTTPS 대신 HTTP로 접근하도록 맞췄다.`

요약:
- 원본: `raw/sources/docker-registry-http-https-mismatch-log.md`
- 상황: Docker registry 컨테이너는 다른 서버에서 실행 중이었다.
- 해결 요약: Docker Desktop Engine 설정에 `insecure-registries`로 `192.168.203.139:5858`을 등록했다.

---

## 검색 태그

docker, registry, tls, certificate, insecure-registry, desktop, self-signed, port

---
