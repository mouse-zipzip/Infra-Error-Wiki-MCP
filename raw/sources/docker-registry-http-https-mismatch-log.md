# Docker private registry push 실패 기록

## 발생한 오류

로컬 네트워크에서 private Docker registry에 이미지를 push하려고 했는데 실패했다.

실행한 명령어:

```bash
docker push 192.168.203.139:5858/test-api:latest
```

처음에는 registry 주소나 포트를 잘못 쓴 줄 알았다.

에러 메시지:

```text
Error response from daemon: Get "https://192.168.203.139:5858/v2/": http: server gave HTTP response to HTTPS client
```

다른 시도에서는 아래처럼 나왔다.

```text
Error response from daemon: Get http://192.168.203.139:5858/v2/: malformed HTTP response "\x15\x03\x01\x00\x02\x02"
```

## 당시 상황

Docker registry 컨테이너는 다른 서버에서 실행 중이었다.

registry 서버 IP:

```text
192.168.203.139
```

사용한 포트:

```text
5858
```

registry 컨테이너는 대충 이런 식으로 띄웠던 것 같다.

```bash
docker run -d -p 5858:5000 --name registry registry:2
```

같은 네트워크 안에 있는 Windows PC에서 Docker Desktop으로 이미지를 push하려고 했다.

이미지 태그는 아래처럼 붙였다.

```bash
docker tag test-api:latest 192.168.203.139:5858/test-api:latest
```

## 확인한 내용

registry 컨테이너가 떠 있는지는 확인했다.

```bash
docker ps
```

포트도 열려 있는 것처럼 보였다.

```text
0.0.0.0:5858->5000/tcp
```

브라우저에서 아래 주소로 접속했을 때는 빈 JSON 비슷한 응답이 나왔다.

```text
http://192.168.203.139:5858/v2/
```

curl로도 HTTP 요청은 되는 것 같았다.

```bash
curl http://192.168.203.139:5858/v2/
```

그런데 Docker push는 계속 실패했다.

처음에는 방화벽 문제나 포트 문제라고 생각했다.

그래서 포트도 바꿔보고, registry 컨테이너도 다시 띄워봤는데 에러가 계속 비슷하게 나왔다.

## 해결 방법

registry 컨테이너 재시작:

```bash
docker restart registry
```

이미지 태그 다시 설정:

```bash
docker tag test-api:latest 192.168.203.139:5858/test-api:latest
```

push 재시도:

```bash
docker push 192.168.203.139:5858/test-api:latest
```

그래도 실패했다.

Docker Desktop 설정을 보다가 Docker Engine JSON 설정에 `insecure-registries`를 추가해야 한다는 글을 봤다.

Docker Desktop → Settings → Docker Engine에서 아래 내용을 추가했다.

```json
{
  "insecure-registries": [
    "192.168.203.139:5858"
  ]
}
```

설정 저장 후 Docker Desktop을 재시작했다.

- Docker Desktop Engine 설정에 `insecure-registries`로 `192.168.203.139:5858`을 등록했다.
- 설정 저장 후 Docker Desktop을 재시작했다.
- 개발용 HTTP registry이므로 Docker client가 해당 registry에 HTTPS 대신 HTTP로 접근하도록 맞췄다.

해결 후 다시 push했더니 정상적으로 올라갔다.


```bash
docker push 192.168.203.139:5858/test-api:latest
```

이후 pull도 정상 동작했다.

```bash
docker pull 192.168.203.139:5858/test-api:latest
```

## 원인

registry는 HTTP로 열려 있었는데 Docker client가 기본적으로 HTTPS registry처럼 접근하려고 해서 문제가 난 것 같다.

`http: server gave HTTP response to HTTPS client`는 HTTPS로 접속했는데 서버가 HTTP 응답을 줬다는 의미로 보인다.

`malformed HTTP response "\x15\x03\x01..."`도 HTTP/HTTPS가 서로 안 맞아서 TLS handshake 데이터를 HTTP 응답처럼 해석하려고 한 문제 같았다.

개발용 registry라서 일단 `insecure-registries`에 등록해서 해결했다.

운영 환경이면 insecure registry로 쓰면 안 되고 TLS 인증서를 제대로 설정해야 할 것 같다.

## 나중에 확인할 것

- 이 registry가 HTTP인지 HTTPS인지 먼저 확인하기
- Docker Desktop의 insecure-registries 설정 확인하기
- 설정 바꾼 뒤 Docker Desktop 재시작했는지 확인하기
- 운영 환경이면 self-signed 말고 제대로 된 TLS 인증서 사용하기

## 관련 키워드

- docker
- registry
- private registry
- insecure registry
- http
- https
- tls
- certificate
- Docker Desktop
- malformed HTTP response
