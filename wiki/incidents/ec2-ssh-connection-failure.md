# EC2 SSH Connection Failure

## 대표 증상

- `Permission denied (publickey)`
- `Network error: Connection timed out`
- `Host key verification failed`
- `WARNING: UNPROTECTED PRIVATE KEY FILE!`

- `@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @`
- `Host key verification failed.`

- SSH 키 파일(`.pem`)을 분실하여 인스턴스에 접근 불가. 명시적 에러는 없으나 인스턴스에 접근할 방법이 없는 상태.

- `Permission denied (publickey).`
- `Authentication failed, permission denied`
- `또는:`

- `@ WARNING: UNPROTECTED PRIVATE KEY FILE! @`

---

## 원인

SSH 공개 키 인증 실패, 키 파일 권한 설정 오류, 보안 그룹 누락, known_hosts 불일치 등 다양한 원인이 있습니다.

---

## 원인 유형

### EC2 Linux 인스턴스 SSH 연결 타임아웃

증상:
- `Network error: Connection timed out`

원인:
- 보안 그룹에 현재 IP에서 포트 22로의 인바운드 규칙 없음
- `서브넷 라우팅 테이블에 Internet Gateway가 없어 인터넷 통신 불가`
- `네트워크 ACL이 SSH 트래픽을 차단`
- 인스턴스에 퍼블릭 IP가 없음
- `인스턴스 CPU 과부하로 SSH 세션 거부`

확인:
1. 0.0.0.0/0 (전체 허용) 또는 현재 IP의 /32 규칙이 있어야 함
2. 0.0.0.0/0 목적지에 Internet Gateway(igw-xxx)가 연결되어 있는지 확인

해결:
- 보안 그룹에 인바운드 규칙 추가
- `서브넷에 Internet Gateway 라우트 추가`
- `Elastic IP 할당 (퍼블릭 IP가 없는 경우)`

요약:
- 원본: `raw/sources/ec2-ssh-connection-timed-out.md`
- 상황: EC2 인스턴스를 새로 시작하거나, 잠시 접속하지 않다가 재접속할 때 발생
- 해결 요약: 보안 그룹에 인바운드 규칙 추가

---

### EC2 SSH 연결 시 Host key verification failed

증상:
- `@ WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED! @`
- `Host key verification failed.`

원인:
- `Elastic IP 추가/제거로 IP 주소가 변경됨`
- 인스턴스를 종료하고 새 인스턴스 시작 (호스트 키 새로 생성됨)
- `EC2 Instance Connect 사용 시 인스턴스 호스트 키가 갱신되었으나 AWS 데이터베이스에 업로드되지 않음`

확인:
1. 로컬 known_hosts 파일에 저장된 호스트 키와 현재 서버의 호스트 키를 비교

해결:
- `방법 1: known_hosts에서 기존 항목 제거`
- `방법 2: EC2 Instance Connect - 호스트 키 업로드`

요약:
- 원본: `raw/sources/ec2-ssh-host-key-verification-failed.md`
- 상황: 이전에 접속했던 EC2 인스턴스에 다시 SSH 연결을 시도할 때 발생
- 해결 요약: 방법 1: known_hosts에서 기존 항목 제거

---

### EC2 인스턴스 SSH 개인 키 분실 후 재접근

증상:
- SSH 키 파일(`.pem`)을 분실하여 인스턴스에 접근 불가. 명시적 에러는 없으나 인스턴스에 접근할 방법이 없는 상태.

원인:
EC2 인스턴스의 SSH 인증은 키 페어 기반 공개 키 인증을 사용함. 개인 키 파일을 분실하면 해당 키를 사용하는 공개 키 인증이 불가능하여 SSH 접근이 차단됨.

확인:
1. EC2 콘솔 → 인스턴스 → Storage 탭 → Root device details → Root device type 항목이 EBS 인지 확인.
2. 루트 볼륨 디바이스 이름 (예: /dev/xvda)

해결:
- `1단계: 새 키 페어 생성`
- `2단계: 원래 인스턴스 중지`
- `3단계: 루트 볼륨 분리`
- `4단계: 임시 인스턴스 시작`
- `5단계: 루트 볼륨을 임시 인스턴스에 데이터 볼륨으로 연결`
- `6단계: 임시 인스턴스에서 authorized_keys 교체`
- `7단계: 볼륨을 원래 인스턴스에 재연결`
- `8단계: 원래 인스턴스 시작 및 접속 확인`
- `9단계: 임시 인스턴스 종료`

요약:
- 원본: `raw/sources/ec2-ssh-lost-private-key.md`
- 상황: `.pem` 파일을 삭제하거나 분실하여 해당 인스턴스에 더 이상 SSH 접속 불가
- 해결 요약: 1단계: 새 키 페어 생성

---

### EC2 Linux 인스턴스 SSH Permission denied (publickey)

증상:
- `Permission denied (publickey).`
- `Authentication failed, permission denied`
- `또는:`

원인:
- 잘못된 사용자명 사용 (예: `root` 대신 `ec2-user`)
- 잘못된 키 파일 사용 (인스턴스 생성 시 지정한 키 파일과 다름)
- 홈 디렉토리 또는 `.ssh/authorized_keys` 권한이 너무 넓어 SSH 서버가 키를 무시
- `DSA 키 사용 (EC2는 RSA 키만 지원)`

확인:
1. EC2 콘솔 → 인스턴스 → Details 탭 → Key pair name 확인. 해당 키 파일(.pem)을 사용하고 있는지 확인.
2. Authentications that can continue: publickey → 공개 키 인증 시도 중
3. Permission denied (publickey) → 서버가 키를 거부함
4. ~/.ssh/ : 700
5. ~/.ssh/authorized_keys : 600

해결:
- 잘못된 사용자명인 경우
- 홈 디렉토리 권한 문제인 경우 (임시 인스턴스 사용)
- 키를 분실한 경우

요약:
- 원본: `raw/sources/ec2-ssh-permission-denied.md`
- 상황: EC2 인스턴스에 SSH로 접속할 때 발생
- 해결 요약: 잘못된 사용자명인 경우

---

### EC2 SSH 연결 시 UNPROTECTED PRIVATE KEY FILE 경고

증상:
- `@ WARNING: UNPROTECTED PRIVATE KEY FILE! @`
- `Permission denied (publickey).`

원인:
SSH 클라이언트는 개인 키 파일에 소유자 외의 사용자(그룹 또는 기타)가 접근 가능한 권한(`0777`, `0755`, `0644` 등)이 설정되어 있으면 보안 위협으로 판단하여 해당 키를 사용하지 않음.

해결:
- `Mac/Linux`
- `Windows (PowerShell)`

요약:
- 원본: `raw/sources/ec2-ssh-unprotected-key-file.md`
- 상황: `.pem` 키 파일을 다운로드하거나 다른 곳에서 복사한 후 SSH 연결을 시도할 때 발생
- 해결 요약: Mac/Linux

---

## 검색 태그

ec2, ssh, key, connection, publickey, port

---
