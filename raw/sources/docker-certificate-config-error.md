# Docker private registry 연결 시 TLS 인증서 오류

## 발생한 오류

```
Error response from daemon: Get http://192.168.203.139:5858/v2/: malformed HTTP response "\x15\x03\x01\x00\x02\x02"
```

private registry에서 이미지를 pull하거나 push할 때 위와 같은 응답 파싱 오류가 발생하며 연결 실패.

## 당시 상황

- 사내 또는 로컬에서 운영하는 private Docker registry에 접근할 때 발생
- self-signed 인증서를 사용하는 HTTPS registry 또는 HTTP로 접근해야 하는 insecure registry 환경에서 발생

## 확인한 내용

Docker 데몬이 해당 registry를 insecure registry 또는 TLS 예외 대상으로 인식하고 있는지 확인:

```bash
# Docker 데몬 설정 확인
cat /etc/docker/daemon.json

# Docker 클라이언트 설정 확인 (certs.d 디렉토리)
ls /etc/docker/certs.d/
```

실제 registry가 HTTP 응답을 기대하는데 Docker가 HTTPS로 요청하고 있거나, HTTPS 응답에서 인증서 검증이 실패하는 경우 위 오류가 발생함.

## 원인

`malformed HTTP response "\x15\x03\x01..."` 메시지는 TLS handshake 응답을 HTTP 파서가 처리하지 못할 때 나타나는 전형적인 증상. 아래 중 하나에 해당:

- Docker 데몬이 HTTP로 요청했으나 서버가 TLS를 강제함
- self-signed 인증서를 사용하는 registry에 대한 CA 인증서가 Docker에 등록되어 있지 않음
- Docker가 클라이언트 인증서를 서버에 전달하지 않음

## 해결 방법

**방법 1: self-signed CA 인증서를 Docker에 등록 (HTTPS 유지)**

```bash
# registry 주소가 192.168.203.139:5858 인 경우
sudo mkdir -p /etc/docker/certs.d/192.168.203.139:5858
sudo cp ca.crt /etc/docker/certs.d/192.168.203.139:5858/ca.crt
sudo systemctl restart docker
```

**방법 2: insecure registry로 등록 (개발/테스트 환경)**

`/etc/docker/daemon.json` 파일 수정:

```json
{
  "insecure-registries": ["192.168.203.139:5858"]
}
```

```bash
sudo systemctl restart docker
```

**방법 3: registry를 올바른 TLS 인증서로 재구성**

공개 CA 또는 Let's Encrypt 인증서를 사용하여 registry를 HTTPS로 올바르게 구성함.

## 재발 방지

- 운영 환경에서는 공인 CA 인증서를 사용한 HTTPS registry를 사용하는 것을 권장
- self-signed 인증서를 사용하는 경우, 팀 전체의 개발 환경에 CA 인증서 배포를 자동화함
- `insecure-registries` 설정은 개발 환경에만 사용하고 운영 환경에서는 사용하지 않음

## 참고

- https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/
- https://docs.docker.com/engine/security/certificates/
