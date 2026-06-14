# EC2 Linux 인스턴스 파일 시스템 체크 실패로 부팅 중단

## 발생한 오류

시스템 로그에 다음 항목이 나타나며 부팅이 중단됨:

```
[/sbin/fsck.ext3 (1) -- /mnt/dbbackups] fsck.ext3 -a /dev/sdh
fsck.ext3: No such file or directory while trying to open /dev/sdh

*** An error occurred during the file system check.
*** Dropping you to a shell; the system will reboot when you leave the shell.
Give root password for maintenance (or type Control-D to continue):
```

또는:

```
/sbin/fsck.xfs: /dev/sdh does not exist
fsck died with exit status 8
failed (code 8).
```

EC2 콘솔에서 인스턴스 상태 체크 실패 표시. 인스턴스가 running 상태이나 SSH 연결 불가.

## 당시 상황

- `/etc/fstab`에 등록된 디바이스가 실제로 연결되어 있지 않은 상태에서 부팅 시 발생
- EBS 볼륨을 분리(Detach)하거나 볼륨 ID가 변경된 후 인스턴스를 재시작할 때 발생
- `fsck`의 6번째 필드(fsck pass 번호)가 0이 아닌 값으로 설정된 항목이 `/etc/fstab`에 있는 경우

## 확인한 내용

EC2 콘솔에서 시스템 로그 확인:

1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `fsck`, `No such file or directory`, `fsck died with exit status` 키워드 검색

임시 인스턴스에서 원래 인스턴스의 루트 볼륨을 마운트하여 `/etc/fstab` 내용 확인:

```bash
sudo mount /dev/xvdf1 /mnt
cat /mnt/etc/fstab
```

`/etc/fstab`의 6번째 필드가 1 또는 2인 항목 중 실제 디바이스가 없는 것을 찾음.

## 원인

- `/etc/fstab`에 등록된 디바이스(`/dev/sdh` 등)가 실제 연결되어 있지 않음
- `fsck` 패스 번호(6번째 필드)가 0이 아닌 경우 부팅 시 해당 파티션에 fsck를 강제 실행하며, 디바이스가 없으면 오류 발생
- `/etc/fstab`의 버그 또는 잘못된 설정

## 해결 방법

**임시 인스턴스를 사용하여 `/etc/fstab` 수정:**

1. 문제 인스턴스 중지
2. 루트 볼륨 분리
3. 임시 인스턴스에 데이터 볼륨으로 연결 (같은 AZ)
4. 루트 볼륨 마운트 후 `/etc/fstab` 수정:

```bash
sudo mount /dev/xvdf1 /mnt
sudo vi /mnt/etc/fstab
```

**`/etc/fstab` 수정 방법:**

존재하지 않는 디바이스의 줄을 주석 처리하거나 삭제:

```
# /dev/sdh /mnt/dbbackups ext3 defaults 0 0  ← 이 줄 주석 처리
```

또는 `nofail` 옵션 추가 (마운트 실패 시 부팅 계속):

```
/dev/sdh /mnt/dbbackups ext3 defaults,nofail 0 0
```

또는 6번째 필드를 0으로 변경 (fsck 비활성화):

```
/dev/sdh /mnt/dbbackups ext3 defaults 0 0
```

5. 언마운트 후 원래 인스턴스에 재연결하여 시작

## 재발 방지

- `/etc/fstab`에 EBS 볼륨을 등록할 때는 6번째 필드를 `0`으로 설정하거나 `nofail` 옵션 사용
- 볼륨 분리 전에 `/etc/fstab`에서 해당 볼륨 항목을 제거하거나 주석 처리
- `/etc/fstab` 변경 후 `sudo mount -a` 로 파싱 오류 없는지 사전 테스트

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstances.html
