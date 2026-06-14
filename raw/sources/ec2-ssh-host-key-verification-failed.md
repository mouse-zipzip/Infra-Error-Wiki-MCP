# EC2 SSH 연결 시 Host key verification failed

## 발생한 오류

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
IT IS POSSIBLE THAT SOMEONE IS DOING SOMETHING NASTY!
...
Host key verification failed.
```

## 당시 상황

- 이전에 접속했던 EC2 인스턴스에 다시 SSH 연결을 시도할 때 발생
- Elastic IP를 추가하거나 제거한 후 다른 IP로 접속할 때 발생
- 인스턴스를 종료하고 같은 도메인 이름이나 IP로 새 인스턴스를 시작했을 때 발생
- EC2 Instance Connect를 통해 인스턴스에 접속할 때 "Error: Host key validation failed" 오류가 나타남

## 확인한 내용

로컬 `known_hosts` 파일에 저장된 호스트 키와 현재 서버의 호스트 키를 비교:

```bash
ssh-keygen -l -F <hostname-or-ip>
```

서버에서 현재 호스트 키 지문 확인 (EC2 콘솔):

EC2 콘솔 → 인스턴스 → Actions → Monitor and troubleshoot → Get system log에서 호스트 키 지문 확인 가능.

또는 EC2 콘솔 → 인스턴스 → 연결 탭에서 EC2 Instance Connect의 호스트 키 정보 확인.

## 원인

SSH 클라이언트는 처음 접속 시 서버의 호스트 키를 `~/.ssh/known_hosts`에 저장함. 이후 같은 IP나 호스트명으로 다시 접속할 때 저장된 키와 다른 키가 제시되면 오류 발생.

원인:
- Elastic IP 추가/제거로 IP 주소가 변경됨
- 인스턴스를 종료하고 새 인스턴스 시작 (호스트 키 새로 생성됨)
- EC2 Instance Connect 사용 시 인스턴스 호스트 키가 갱신되었으나 AWS 데이터베이스에 업로드되지 않음

## 해결 방법

**방법 1: known_hosts에서 기존 항목 제거**

변경이 의도적인 경우(새 인스턴스, Elastic IP 변경 등):

```bash
ssh-keygen -R <hostname-or-ip>
```

또는 `~/.ssh/known_hosts` 파일에서 해당 호스트 줄을 직접 삭제 후 재접속.

재접속 시 새 호스트 키 지문을 확인하고 `yes`를 입력하면 새 키가 등록됨.

**방법 2: EC2 Instance Connect - 호스트 키 업로드**

EC2 Instance Connect 브라우저 클라이언트에서 오류가 난 경우, 인스턴스에 SSH로 접속하여 스크립트 실행:

Amazon Linux 2:

```bash
cd /opt/aws/bin/
sudo ./eic_harvest_hostkeys
```

Ubuntu:

```bash
cd /usr/share/ec2-instance-connect/
sudo ./eic_harvest_hostkeys
```

## 재발 방지

- 인스턴스를 교체할 때는 `ssh-keygen -R <old-ip>`를 먼저 실행하는 것을 절차에 포함
- 인스턴스 호스트 키를 교체(rotate)한 경우 즉시 `eic_harvest_hostkeys`를 실행하여 AWS에 업로드
- 고정 IP(Elastic IP)를 사용하면 IP 변경으로 인한 호스트 키 불일치를 줄일 수 있음

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstancesConnecting.html
