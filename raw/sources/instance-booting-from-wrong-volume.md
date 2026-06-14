# EC2 인스턴스가 잘못된 볼륨으로 부팅됨

## 발생한 오류

인스턴스가 의도한 루트 볼륨(`/dev/xvda`) 대신 다른 볼륨으로 부팅됨. 직접적인 에러 메시지는 없으나, 부팅 후 파일 시스템이나 설정이 예상과 다른 상태로 나타남.

두 볼륨의 label이 동일하게 `/`로 보임:

```bash
[ec2-user ~]$ sudo e2label /dev/xvda1
/
[ec2-user ~]$ sudo e2label /dev/xvdf1
/
```

스냅샷에서 생성된 볼륨의 경우 UUID도 동일하게 나올 수 있음:

```bash
[ec2-user ~]$ sudo blkid
/dev/xvda1: LABEL="/" UUID=73947a77-ddbe-4dc7-bd8f-3fe0bc840778 TYPE="ext4"
/dev/xvdf1: LABEL="/" UUID=73947a77-ddbe-4dc7-bd8f-3fe0bc840778 TYPE="ext4"
```

## 당시 상황

다른 인스턴스의 루트 볼륨(또는 그 스냅샷으로 만든 볼륨)을 현재 인스턴스에 추가로 마운트한 상태에서 인스턴스를 재부팅했을 때 발생. `/etc/fstab`에서 `LABEL=/`로 루트를 정의하고 있는 환경에서 발생 빈도 높음.

## 확인한 내용

`e2label` 또는 `blkid`로 연결된 볼륨들의 label과 UUID 비교:

```bash
sudo e2label /dev/xvda1
sudo e2label /dev/xvdf1
sudo blkid
```

`/etc/fstab` 확인:

```bash
cat /etc/fstab
```

`LABEL=/` 방식으로 루트를 정의하고 있으면, 동일 label을 가진 볼륨이 여러 개일 때 ramdisk가 잘못된 볼륨을 선택할 수 있음.

## 원인

Linux initial ramdisk는 `/etc/fstab`에 정의된 label 또는 UUID를 기준으로 루트 볼륨을 선택함. 다른 인스턴스의 루트 볼륨이나 동일 스냅샷으로 만든 볼륨을 연결하면, 두 볼륨이 같은 label(`/`)과 UUID를 가질 수 있고, 이 경우 ramdisk가 의도하지 않은 볼륨을 루트로 선택함.

## 해결 방법

부팅 대상이 **아닌** 볼륨의 label을 변경해 충돌을 해소함.

**ext4 파일 시스템인 경우 (`e2label`):**

```bash
sudo e2label /dev/xvdf1 old/
```

변경 확인:

```bash
sudo e2label /dev/xvdf1
# old/
```

**xfs 파일 시스템인 경우 (`xfs_admin`):**

```bash
sudo xfs_admin -L old/ /dev/xvdf1
# writing all SBs
# new label = "old/"
```

label 변경 후 인스턴스를 재부팅하면 정상 볼륨으로 부팅됨.

## 재발 방지

- 다른 인스턴스의 루트 볼륨을 임시 마운트할 때는 마운트 전에 반드시 해당 볼륨의 label을 변경함.
- 원래 인스턴스에 볼륨을 돌려줄 때는 label을 다시 `/`로 복원하는 것을 잊지 않음.
- `/etc/fstab`에서 루트 볼륨을 `LABEL=/` 대신 `/dev/xvda1` 같은 디바이스 경로로 지정하거나, 볼륨별로 고유한 label을 사용하면 이 문제를 근본적으로 방지할 수 있음.

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-booting-from-wrong-volume.html
