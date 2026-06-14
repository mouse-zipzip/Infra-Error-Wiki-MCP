# EC2 Linux 인스턴스 SSH Permission denied (publickey)

## 발생한 오류

```
Permission denied (publickey).
```

또는:

```
Host key not found in [directory]
Authentication failed, permission denied
Connection closed by [instance] port 22
```

## 당시 상황

- EC2 인스턴스에 SSH로 접속할 때 발생
- 처음 생성된 인스턴스에 접속하거나, 키 파일을 변경한 후 접속할 때 발생
- 이전에 잘 접속되던 인스턴스에 갑자기 접근 불가해진 경우 (홈 디렉토리 권한 변경 등)

## 확인한 내용

**1. 올바른 사용자명 사용 여부 확인**

AMI별 기본 사용자명:

| AMI | 기본 사용자명 |
|---|---|
| Amazon Linux | ec2-user |
| Ubuntu | ubuntu |
| CentOS | centos 또는 ec2-user |
| RHEL | ec2-user 또는 root |
| Debian | admin |

**2. 올바른 키 파일 사용 여부**

EC2 콘솔 → 인스턴스 → Details 탭 → Key pair name 확인. 해당 키 파일(`.pem`)을 사용하고 있는지 확인.

**3. 상세 디버그 로그로 확인**

```bash
ssh -vvv -i /path/to/key.pem ec2-user@<public-ip>
```

`Authentications that can continue: publickey` → 공개 키 인증 시도 중
`Permission denied (publickey)` → 서버가 키를 거부함

**4. 홈 디렉토리 권한 확인 (이전에 접속되던 인스턴스)**

권한이 잘못된 경우 SSH 서버가 authorized_keys를 무시함. 필요한 권한:
- `~/.ssh/` : 700
- `~/.ssh/authorized_keys` : 600
- `~/` (홈 디렉토리) : 700

## 원인

- 잘못된 사용자명 사용 (예: `root` 대신 `ec2-user`)
- 잘못된 키 파일 사용 (인스턴스 생성 시 지정한 키 파일과 다름)
- 홈 디렉토리 또는 `.ssh/authorized_keys` 권한이 너무 넓어 SSH 서버가 키를 무시
- DSA 키 사용 (EC2는 RSA 키만 지원)

## 해결 방법

**잘못된 사용자명인 경우:**

```bash
ssh -i key.pem ec2-user@<ip>   # Amazon Linux
ssh -i key.pem ubuntu@<ip>     # Ubuntu
```

**홈 디렉토리 권한 문제인 경우 (임시 인스턴스 사용):**

1. 문제 인스턴스 중지 → 루트 볼륨 분리
2. 임시 인스턴스에 연결 후 마운트:

```bash
sudo mount /dev/xvdf1 /mnt
```

3. 권한 수정:

```bash
sudo chmod 700 /mnt/home/ec2-user/.ssh
sudo chmod 600 /mnt/home/ec2-user/.ssh/authorized_keys
sudo chmod 700 /mnt/home/ec2-user
```

4. 언마운트 후 원래 인스턴스에 재연결하여 시작

**키를 분실한 경우:**

새 키 페어를 생성한 후 임시 인스턴스를 사용하여 `authorized_keys` 파일을 교체함. (상세 절차는 `ec2-ssh-lost-private-key.md` 참조)

## 재발 방지

- 처음 인스턴스에 접속할 때 키 파일 경로와 사용자명을 정확히 확인
- 홈 디렉토리 권한을 변경하는 스크립트나 배포 작업 후 SSH 접속 테스트
- `~/.ssh/` 디렉토리와 `authorized_keys` 파일 권한을 cron 또는 배포 파이프라인에서 자동 점검

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstancesConnecting.html
