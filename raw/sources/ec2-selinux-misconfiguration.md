# EC2 Linux 인스턴스 SELinux 설정 오류로 부팅 중단

## 발생한 오류

시스템 로그에 다음 항목이 나타나며 부팅이 중단됨:

```
audit(1313445102.626:2): enforcing=1 old_enforcing=0 auid=4294967295
Unable to load SELinux Policy. Machine is in enforcing mode. Halting now.
Kernel panic - not syncing: Attempted to kill init!
```

EC2 콘솔에서 인스턴스 상태 체크 실패 표시. 인스턴스가 running 상태이나 SSH 연결 불가.

## 당시 상황

- SELinux가 비활성화(permissive 또는 disabled)된 AMI에서 실행하다가 enforcing 모드로 변경 후 재부팅할 때 발생
- SELinux policy 파일이 없거나 잘못 설치된 상태에서 enforcing 모드로 설정된 경우
- 커널 파라미터나 설정 파일을 수동으로 변경한 후 발생

## 확인한 내용

EC2 콘솔에서 시스템 로그 확인:

1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `SELinux`, `Unable to load SELinux Policy`, `enforcing` 키워드 검색

임시 인스턴스에서 루트 볼륨 마운트 후 SELinux 설정 파일 확인:

```bash
sudo mount /dev/xvdf1 /mnt
cat /mnt/etc/selinux/config
# SELINUX=enforcing 인 경우 문제
```

## 원인

- SELinux가 enforcing 모드로 설정되어 있으나, 해당 환경에 SELinux policy가 설치되어 있지 않거나 손상됨
- `/etc/selinux/config`에서 `SELINUX=enforcing`으로 변경했으나 policy 준비가 되지 않은 경우
- SELinux policy와 호환되지 않는 커널로 변경된 경우

## 해결 방법

임시 인스턴스에서 루트 볼륨을 마운트하여 SELinux 설정 변경:

**1. 문제 인스턴스 중지 후 루트 볼륨 분리**

**2. 임시 인스턴스에 데이터 볼륨으로 연결 후 마운트:**

```bash
sudo mount /dev/xvdf1 /mnt
```

**3. SELinux 설정을 permissive 또는 disabled로 변경:**

```bash
sudo vi /mnt/etc/selinux/config
```

변경:

```
# SELINUX=enforcing  ← 이 줄을 아래로 변경
SELINUX=permissive
```

또는:

```
SELINUX=disabled
```

**4. 언마운트 후 원래 인스턴스에 재연결하여 시작**

부팅 성공 후, 필요한 경우 SELinux policy를 올바르게 설치하고 enforcing 모드 재적용:

```bash
sudo yum install selinux-policy selinux-policy-targeted  # RHEL/CentOS
sudo touch /.autorelabel  # 다음 부팅 시 파일 시스템 재레이블링
sudo reboot
```

## 재발 방지

- SELinux 모드 변경 전 `sudo semanage permissive -l`로 현재 상태 확인
- enforcing 모드로 변경하기 전 policy 설치 및 테스트를 permissive 모드에서 먼저 진행
- EC2 AMI 중 SELinux를 지원하지 않는 AMI에서는 SELinux 관련 설정을 변경하지 않음

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstances.html
