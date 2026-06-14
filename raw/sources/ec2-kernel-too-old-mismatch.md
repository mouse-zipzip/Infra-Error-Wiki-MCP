# EC2 Linux 인스턴스 커널-AMI 불일치로 부팅 실패

## 발생한 오류

시스템 로그에 다음 항목이 나타나며 부팅이 중단됨:

```
FATAL: kernel too old
Kernel panic - not syncing: Attempted to kill init!
```

또는 커널 모듈 로드 실패:

```
FATAL: Could not load /lib/modules/2.6.34-4-virtual/modules.dep: No such file or directory
ALERT! /dev/sda1 does not exist. Dropping to a shell!
BusyBox v1.13.3 (Ubuntu 1:1.13.3-1ubuntu5) built-in shell (ash)
(initramfs)
```

EC2 콘솔에서 인스턴스 상태 체크 실패 표시. 인스턴스가 running 상태이나 SSH 연결 불가.

## 당시 상황

- 인스턴스의 커널을 업그레이드하거나 변경한 후 재부팅했을 때 발생
- AMI를 변경하여 인스턴스를 재시작했을 때, 기존 커널이 새 AMI의 userland와 호환되지 않는 경우
- 매우 오래된 커널(예: 2.6.16-xenU)을 사용하는 인스턴스에서 발생

## 확인한 내용

EC2 콘솔에서 시스템 로그 확인:

1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `FATAL: kernel too old`, `BusyBox`, `FATAL: Could not load /lib/modules` 키워드 검색

현재 커널 버전과 AMI의 예상 커널 버전 불일치 여부 확인.

## 원인

- **커널 너무 오래됨:** 현재 커널이 AMI의 userland(glibc 등)가 요구하는 최소 버전을 충족하지 못함
- **커널 모듈 없음:** initramfs/ramdisk에 포함된 커널과 실제 설치된 커널 버전이 달라 모듈 로드 실패
- **ramdisk 문제:** EBS 루트 볼륨이 `/dev/sda1`으로 올바르게 연결되지 않음

## 해결 방법

**EBS 기반 인스턴스 (데이터 복구 가능):**

1. 문제 인스턴스 중지
2. 루트 볼륨 분리(Detach)
3. 임시 인스턴스를 같은 AZ에 생성하여 볼륨을 데이터 볼륨으로 연결
4. 임시 인스턴스에서 볼륨 마운트 후 커널/grub 설정 수정:

```bash
sudo mount /dev/xvdf1 /mnt
sudo chroot /mnt
# 올바른 커널 설치 또는 grub 설정 수정
apt-get install linux-image-generic  # Ubuntu 예시
update-grub
exit
sudo umount /mnt
```

5. 볼륨을 원래 인스턴스에 다시 연결 후 시작

**Instance store 기반 인스턴스 (데이터 복구 불가):**

인스턴스를 종료하고 올바른 커널 버전을 가진 새 AMI로 재시작.

## 재발 방지

- 커널 업그레이드 후 반드시 EBS 스냅샷을 생성하고 재부팅 테스트 진행
- AMI 변경 시 새 AMI가 요구하는 커널 버전과 현재 커널 버전 호환성을 사전에 확인
- 오래된 커널(2.6.x xenU 계열)을 사용하는 인스턴스는 현대적인 HVM AMI로 마이그레이션

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstances.html
