# EC2 인스턴스 SSH 개인 키 분실 후 재접근

## 발생한 오류

SSH 키 파일(`.pem`)을 분실하여 인스턴스에 접근 불가. 명시적 에러는 없으나 인스턴스에 접근할 방법이 없는 상태.

## 당시 상황

- `.pem` 파일을 삭제하거나 분실하여 해당 인스턴스에 더 이상 SSH 접속 불가
- 팀원이 키를 관리하다 퇴사하거나 키 파일 관리를 하지 않은 경우
- 키 페어를 선택하지 않고 인스턴스를 생성했거나, 원래 키를 잊어버린 경우

해당 절차는 **EBS 루트 볼륨을 사용하는 인스턴스**에만 적용됨. Instance store 루트 볼륨은 이 방법으로 복구 불가.

## 확인한 내용

인스턴스의 루트 볼륨 타입 확인:

EC2 콘솔 → 인스턴스 → Storage 탭 → Root device details → Root device type 항목이 `EBS` 인지 확인.

인스턴스 정보 기록:
- 인스턴스 ID
- AMI ID
- 가용 영역(Availability Zone)
- 루트 볼륨 ID (예: vol-0a1234b5678c910de)
- 루트 볼륨 디바이스 이름 (예: `/dev/xvda`)

## 원인

EC2 인스턴스의 SSH 인증은 키 페어 기반 공개 키 인증을 사용함. 개인 키 파일을 분실하면 해당 키를 사용하는 공개 키 인증이 불가능하여 SSH 접근이 차단됨.

## 해결 방법

임시 인스턴스를 활용하여 `authorized_keys`를 새 키로 교체하는 절차:

**1단계: 새 키 페어 생성**

EC2 콘솔 → Key Pairs → Create key pair → 새 키 파일 다운로드 및 보관.

**2단계: 원래 인스턴스 중지**

EC2 콘솔 → 인스턴스 → Instance state → Stop instance.

**3단계: 루트 볼륨 분리**

EC2 콘솔 → Volumes → 루트 볼륨 선택 → Actions → Detach volume.

**4단계: 임시 인스턴스 시작**

같은 가용 영역에 임시 인스턴스를 시작. 새 키 페어를 사용하고 접근 가능한 상태로 생성.

**5단계: 루트 볼륨을 임시 인스턴스에 데이터 볼륨으로 연결**

EC2 콘솔 → Volumes → 분리한 볼륨 선택 → Actions → Attach volume → 임시 인스턴스 선택 (디바이스 이름 예: `/dev/sdf`).

**6단계: 임시 인스턴스에서 authorized_keys 교체**

임시 인스턴스에 SSH 접속 후:

```bash
# 파티션 구조 확인
lsblk

# 마운트 디렉토리 생성 후 마운트
sudo mkdir /mnt/tempvol
sudo mount /dev/xvdf1 /mnt/tempvol  # Amazon Linux, Ubuntu, Debian
# Amazon Linux 2, CentOS, RHEL 7.x는 아래 사용:
# sudo mount -o nouuid /dev/xvdf1 /mnt/tempvol

# 임시 인스턴스의 authorized_keys를 원래 볼륨에 복사
cp ~/.ssh/authorized_keys /mnt/tempvol/home/ec2-user/.ssh/authorized_keys

# 언마운트
sudo umount /mnt/tempvol
```

**7단계: 볼륨을 원래 인스턴스에 재연결**

Detach → Attach volume → 원래 인스턴스 선택 → 원래 디바이스 이름(예: `/dev/xvda`)으로 연결.

**8단계: 원래 인스턴스 시작 및 접속 확인**

```bash
ssh -i /path/to/new-key.pem ec2-user@<public-ip>
```

**9단계: 임시 인스턴스 종료**

불필요한 임시 인스턴스를 종료(Terminate).

## 재발 방지

- 키 파일은 팀이 공유할 수 있는 안전한 비밀 관리 시스템(AWS Secrets Manager, HashiCorp Vault, 1Password Teams 등)에 저장
- 인스턴스마다 공유 키가 아닌 개인 키를 사용하고, 정기적으로 키를 교체
- AWS Systems Manager Session Manager를 사용하면 SSH 키 없이도 인스턴스에 접근 가능 → 키 분실 시 대안 경로 확보

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstancesConnecting.html
- https://repost.aws/knowledge-center/user-data-replace-key-pair-ec2
