# EC2 Instance System Error

## 대표 증상

- `Out of memory: kill process`
- `I/O error, dev sde`
- `FATAL: kernel too old`
- `Unable to load SELinux Policy. Machine is in enforcing mode. Halting now.`
- `Device eth0 has different MAC address than expected, ignoring.`
- `EC2 콘솔에서 인스턴스 상태 체크 실패 (System status check failed 또는 Instance status check failed) 표시.`
- `[9943662.053217] end_request: I/O error, dev sde, sector 52428288`
- `[9943664.191262] end_request: I/O error, dev sde, sector 52428168`
- `[9943664.191285] Buffer I/O error on device md0, logical block 209713024`
- `[9943664.191297] Buffer I/O error on device md0, logical block 209713025`

- `*** An error occurred during the file system check.`
- `failed (code 8).`

- `[FAILED]`

- `FATAL: Could not load /lib/modules/2.6.34-4-virtual/modules.dep: No such file or directory`

- `EC2 콘솔에서 인스턴스 상태 체크 실패 (Instance status check failed) 표시.`
- `[115879.769795] Out of memory: kill process 20273 (httpd) score 1285879 or a child`

- `[ec2-user ~]$ sudo e2label /dev/xvda1`

---

## 원인

메모리 고갈, 블록 디바이스 I/O 오류, 커널-AMI 불일치, /etc/fstab 설정 오류, SELinux 설정 오류, MAC 주소 하드코딩, 볼륨 label 충돌 등 다양한 시스템 레벨 원인이 있습니다.

---

## 원인 유형

### EC2 Linux 인스턴스 블록 디바이스 I/O 오류

증상:
- `EC2 콘솔에서 인스턴스 상태 체크 실패 (System status check failed 또는 Instance status check failed) 표시.`
- `[9943662.053217] end_request: I/O error, dev sde, sector 52428288`
- `[9943664.191262] end_request: I/O error, dev sde, sector 52428168`
- `[9943664.191285] Buffer I/O error on device md0, logical block 209713024`
- `[9943664.191297] Buffer I/O error on device md0, logical block 209713025`

원인:
- `EBS 기반: EBS 볼륨 장애 (AWS 인프라 문제)`
- `Instance store 기반: 물리 디스크 장애 (호스트 하드웨어 문제)`

확인:
1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `I/O error`, `Buffer I/O error`, `end_request` 키워드 검색

해결:
- `EBS 기반 인스턴스`
- `Instance store 기반 인스턴스`

요약:
- 원본: `raw/sources/ec2-block-device-io-error.md`
- 상황: 디스크 읽기/쓰기 작업 중 반복적인 I/O 오류가 시스템 로그에 기록됨
- 해결 요약: EBS 기반 인스턴스

---

### EC2 Linux 인스턴스 파일 시스템 체크 실패로 부팅 중단

증상:
- `*** An error occurred during the file system check.`
- `failed (code 8).`

원인:
- `/etc/fstab`에 등록된 디바이스(`/dev/sdh` 등)가 실제 연결되어 있지 않음
- `fsck` 패스 번호(6번째 필드)가 0이 아닌 경우 부팅 시 해당 파티션에 fsck를 강제 실행하며, 디바이스가 없으면 오류 발생
- `/etc/fstab`의 버그 또는 잘못된 설정

확인:
1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `fsck`, `No such file or directory`, `fsck died with exit status` 키워드 검색
3. 임시 인스턴스에서 원래 인스턴스의 루트 볼륨을 마운트하여 /etc/fstab 내용 확인
4. /etc/fstab의 6번째 필드가 1 또는 2인 항목 중 실제 디바이스가 없는 것을 찾음.

해결:
- 임시 인스턴스를 사용하여 `/etc/fstab` 수정
- `/etc/fstab` 수정 방법

요약:
- 원본: `raw/sources/ec2-filesystem-not-found-fsck.md`
- 상황: `/etc/fstab`에 등록된 디바이스가 실제로 연결되어 있지 않은 상태에서 부팅 시 발생
- 해결 요약: 임시 인스턴스를 사용하여 `/etc/fstab` 수정

---

### EC2 Linux 인스턴스 하드코딩된 MAC 주소로 네트워크 인터페이스 초기화 실패

증상:
- `[FAILED]`

원인:
- `/etc/udev/rules.d/70-persistent-net.rules` - udev가 MAC 주소를 인터페이스 이름에 고정
- `/etc/sysconfig/network-scripts/ifcfg-eth0`의 `HWADDR` 항목

확인:
1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `MAC address`, `eth0 has different MAC`, `FAILED` 키워드 검색

해결:
- `방법 1: 임시 인스턴스에서 설정 파일 수정`
- `방법 2: AMI 생성 전 MAC 주소 하드코딩 제거`

요약:
- 원본: `raw/sources/ec2-hardcoded-mac-address.md`
- 상황: AMI를 생성(Create Image)하여 새 인스턴스를 시작할 때 발생
- 해결 요약: 방법 1: 임시 인스턴스에서 설정 파일 수정

---

### EC2 Linux 인스턴스 커널-AMI 불일치로 부팅 실패

증상:
- `FATAL: kernel too old`
- `FATAL: Could not load /lib/modules/2.6.34-4-virtual/modules.dep: No such file or directory`

원인:
- `**커널 너무 오래됨:** 현재 커널이 AMI의 userland(glibc 등)가 요구하는 최소 버전을 충족하지 못함`
- `**커널 모듈 없음:** initramfs/ramdisk에 포함된 커널과 실제 설치된 커널 버전이 달라 모듈 로드 실패`
- **ramdisk 문제:** EBS 루트 볼륨이 `/dev/sda1`으로 올바르게 연결되지 않음

확인:
1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `FATAL: kernel too old`, `BusyBox`, `FATAL: Could not load /lib/modules` 키워드 검색

해결:
- `EBS 기반 인스턴스 (데이터 복구 가능)`
- `Instance store 기반 인스턴스 (데이터 복구 불가)`

요약:
- 원본: `raw/sources/ec2-kernel-too-old-mismatch.md`
- 상황: 인스턴스의 커널을 업그레이드하거나 변경한 후 재부팅했을 때 발생
- 해결 요약: EBS 기반 인스턴스 (데이터 복구 가능)

---

### EC2 Linux 인스턴스 메모리 부족으로 프로세스 강제 종료 (OOM Killer)

증상:
- `EC2 콘솔에서 인스턴스 상태 체크 실패 (Instance status check failed) 표시.`
- `[115879.769795] Out of memory: kill process 20273 (httpd) score 1285879 or a child`

원인:
- 현재 인스턴스 타입의 메모리가 워크로드에 비해 부족
- 애플리케이션 메모리 누수
- 트래픽 폭증으로 인한 프로세스 수 급증

확인:
1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. 로그에서 `Out of memory: kill process` 검색

해결:
- 즉각적 조치
- 근본 해결

요약:
- 원본: `raw/sources/ec2-out-of-memory-kill-process.md`
- 상황: 트래픽 급증 또는 메모리 누수로 인해 인스턴스 메모리가 고갈됨
- 해결 요약: 즉각적 조치

---

### EC2 Linux 인스턴스 SELinux 설정 오류로 부팅 중단

증상:
- `Unable to load SELinux Policy. Machine is in enforcing mode. Halting now.`

원인:
- `SELinux가 enforcing 모드로 설정되어 있으나, 해당 환경에 SELinux policy가 설치되어 있지 않거나 손상됨`
- `/etc/selinux/config`에서 `SELINUX=enforcing`으로 변경했으나 policy 준비가 되지 않은 경우
- `SELinux policy와 호환되지 않는 커널로 변경된 경우`

확인:
1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `SELinux`, `Unable to load SELinux Policy`, `enforcing` 키워드 검색

해결:
- 문제 인스턴스 중지 후 루트 볼륨 분리
- 임시 인스턴스에 데이터 볼륨으로 연결 후 마운트
- `SELinux 설정을 permissive 또는 disabled로 변경`
- 언마운트 후 원래 인스턴스에 재연결하여 시작

요약:
- 원본: `raw/sources/ec2-selinux-misconfiguration.md`
- 상황: SELinux가 비활성화(permissive 또는 disabled)된 AMI에서 실행하다가 enforcing 모드로 변경 후 재부팅할 때 발생
- 해결 요약: 문제 인스턴스 중지 후 루트 볼륨 분리

---

### EC2 인스턴스가 잘못된 볼륨으로 부팅됨

증상:
- `[ec2-user ~]$ sudo e2label /dev/xvda1`

원인:
Linux initial ramdisk는 `/etc/fstab`에 정의된 label 또는 UUID를 기준으로 루트 볼륨을 선택함. 다른 인스턴스의 루트 볼륨이나 동일 스냅샷으로 만든 볼륨을 연결하면, 두 볼륨이 같은 label(`/`)과 UUID를 가질 수 있고, 이 경우 ramdisk가 의도하지 않은 볼륨을 루트로 선택함.

확인:
1. e2label 또는 blkid로 연결된 볼륨들의 label과 UUID 비교
2. /etc/fstab 확인
3. LABEL=/ 방식으로 루트를 정의하고 있으면, 동일 label을 가진 볼륨이 여러 개일 때 ramdisk가 잘못된 볼륨을 선택할 수 있음.

해결:
- ext4 파일 시스템인 경우 (`e2label`)
- xfs 파일 시스템인 경우 (`xfs_admin`)

요약:
- 원본: `raw/sources/instance-booting-from-wrong-volume.md`
- 상황: 다른 인스턴스의 루트 볼륨(또는 그 스냅샷으로 만든 볼륨)을 현재 인스턴스에 추가로 마운트한 상태에서 인스턴스를 재부팅했을 때 발생. `/etc/fstab`에서 `LABEL=/`로 루트를 정의하고 있는 환경에서 발생 빈도 높음.
- 해결 요약: ext4 파일 시스템인 경우 (`e2label`)

---

## 검색 태그

ec2, kernel, filesystem, memory, selinux, volume, boot, port

---
