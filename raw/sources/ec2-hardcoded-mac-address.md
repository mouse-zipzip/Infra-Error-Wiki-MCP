# EC2 Linux 인스턴스 하드코딩된 MAC 주소로 네트워크 인터페이스 초기화 실패

## 발생한 오류

시스템 로그에 다음 항목이 나타남:

```
Bringing up interface eth0: Device eth0 has different MAC address than expected, ignoring.
[FAILED]
```

인스턴스가 시작되지만 네트워크 인터페이스(eth0)를 가져오지 못해 SSH 접근 불가.

## 당시 상황

- AMI를 생성(Create Image)하여 새 인스턴스를 시작할 때 발생
- 인스턴스 타입을 변경하거나 다른 VPC/서브넷에서 인스턴스를 시작할 때 발생
- 인스턴스를 중지 후 재시작할 때 MAC 주소가 변경된 경우

## 확인한 내용

EC2 콘솔에서 시스템 로그 확인:

1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `MAC address`, `eth0 has different MAC`, `FAILED` 키워드 검색

임시 인스턴스에서 루트 볼륨 마운트 후 네트워크 규칙 파일 확인:

```bash
sudo mount /dev/xvdf1 /mnt
# RHEL/CentOS 기반
cat /mnt/etc/udev/rules.d/70-persistent-net.rules
# 또는
cat /mnt/etc/sysconfig/network-scripts/ifcfg-eth0 | grep HWADDR
```

## 원인

AMI 또는 네트워크 설정 파일에 이전 인스턴스의 MAC 주소가 하드코딩되어 있음. 새 인스턴스를 시작하면 새로운 MAC 주소가 할당되는데, 이 주소가 설정 파일의 값과 달라 네트워크 인터페이스가 무시됨.

주요 위치:
- `/etc/udev/rules.d/70-persistent-net.rules` - udev가 MAC 주소를 인터페이스 이름에 고정
- `/etc/sysconfig/network-scripts/ifcfg-eth0`의 `HWADDR` 항목

## 해결 방법

**방법 1: 임시 인스턴스에서 설정 파일 수정**

1. 문제 인스턴스 중지 → 루트 볼륨 분리
2. 임시 인스턴스에 연결 후 마운트:

```bash
sudo mount /dev/xvdf1 /mnt
```

3. MAC 주소 관련 파일 수정:

```bash
# 70-persistent-net.rules 삭제 또는 비워두기
sudo rm /mnt/etc/udev/rules.d/70-persistent-net.rules

# ifcfg-eth0에서 HWADDR 줄 제거
sudo sed -i '/^HWADDR/d' /mnt/etc/sysconfig/network-scripts/ifcfg-eth0
```

4. 언마운트 후 원래 인스턴스에 재연결하여 시작

**방법 2: AMI 생성 전 MAC 주소 하드코딩 제거**

AMI 생성 전 원본 인스턴스에서:

```bash
sudo rm /etc/udev/rules.d/70-persistent-net.rules
sudo sed -i '/^HWADDR/d' /etc/sysconfig/network-scripts/ifcfg-eth0
```

이후 AMI 생성 시 MAC 주소 정보가 포함되지 않음.

## 재발 방지

- AMI 생성 전 `70-persistent-net.rules`와 `HWADDR` 설정을 반드시 제거하는 것을 AMI 생성 체크리스트에 포함
- cloud-init이 올바르게 설정되어 있으면 MAC 주소를 자동으로 처리함 → cloud-init 버전을 최신으로 유지

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstances.html
