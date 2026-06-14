# EC2 Linux 인스턴스 블록 디바이스 I/O 오류

## 발생한 오류

시스템 로그에 다음과 같은 항목이 연속으로 나타남:

```
[9943662.053217] end_request: I/O error, dev sde, sector 52428288
[9943664.191262] end_request: I/O error, dev sde, sector 52428168
[9943664.191285] Buffer I/O error on device md0, logical block 209713024
[9943664.191297] Buffer I/O error on device md0, logical block 209713025
```

또는 분산 블록 디바이스의 경우:

```
block drbd1: Local IO failed in request_timer_fn. Detaching...
block drbd1: IO ERROR: neither local nor remote disk
Buffer I/O error on device drbd1, logical block 557056
JBD2: I/O error detected when updating journal superblock for drbd1-8.
```

EC2 콘솔에서 인스턴스 상태 체크 실패 (System status check failed 또는 Instance status check failed) 표시.

## 당시 상황

- 디스크 읽기/쓰기 작업 중 반복적인 I/O 오류가 시스템 로그에 기록됨
- 애플리케이션에서 파일 읽기/쓰기 실패 또는 데이터베이스 오류 발생
- EBS 볼륨 기반 인스턴스 또는 Instance store 기반 인스턴스 모두에서 발생 가능

## 확인한 내용

EC2 콘솔에서 시스템 로그 확인:

1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. `I/O error`, `Buffer I/O error`, `end_request` 키워드 검색

EBS 볼륨 상태 확인:

EC2 콘솔 → Volumes → 해당 볼륨 선택 → Status checks 탭

인스턴스 재부팅 후 디스크 상태:

```bash
# 파일 시스템 상태 확인
dmesg | grep -i "i/o error"
df -h
```

## 원인

| 인스턴스 타입 | 가능한 원인 |
|---|---|
| EBS 기반 | EBS 볼륨 장애 (AWS 인프라 문제) |
| Instance store 기반 | 물리 디스크 장애 (호스트 하드웨어 문제) |

## 해결 방법

**EBS 기반 인스턴스:**

1. 인스턴스 중지
2. 문제가 있는 EBS 볼륨 분리(Detach)
3. 최근 스냅샷에서 새 볼륨 생성 후 연결
4. 인스턴스 재시작

스냅샷이 없는 경우 AWS Support 문의.

**Instance store 기반 인스턴스:**

Instance store 데이터는 복구 불가. 인스턴스를 종료(Terminate)하고 백업에서 새 인스턴스를 시작.

```bash
# 종료 전 가능하다면 중요 데이터를 S3에 백업
aws s3 cp /important/data s3://my-backup-bucket/ --recursive
```

## 재발 방지

- EBS 볼륨의 정기적 스냅샷 생성 (AWS Backup 또는 Data Lifecycle Manager 사용):
  ```bash
  # 예: 매일 새벽 2시에 스냅샷 생성 (DLM 정책으로 자동화)
  ```
- 중요 데이터는 Instance store가 아닌 EBS에 저장 (Instance store는 인스턴스 종료 시 데이터 소실)
- EBS 볼륨 상태를 CloudWatch `VolumeReadOps`, `VolumeWriteOps` 메트릭으로 모니터링
- 데이터베이스는 Multi-AZ 구성 또는 EBS Multi-Attach를 사용하여 단일 볼륨 장애 대비

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstances.html
- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EBSSnapshots.html
