# EC2 Linux 인스턴스 메모리 부족으로 프로세스 강제 종료 (OOM Killer)

## 발생한 오류

시스템 로그에 다음과 같은 항목이 나타남:

```
[115879.769795] Out of memory: kill process 20273 (httpd) score 1285879 or a child
[115879.769795] Killed process 1917 (php-cgi) vsz:467184kB, anon-rss:101196kB, file-rss:204kB
```

EC2 콘솔에서 인스턴스 상태 체크 실패 (Instance status check failed) 표시.

## 당시 상황

- 트래픽 급증 또는 메모리 누수로 인해 인스턴스 메모리가 고갈됨
- Linux OOM(Out Of Memory) Killer가 점수가 높은 프로세스(주로 애플리케이션 프로세스)를 강제 종료
- 웹 서버(httpd, nginx), 애플리케이션(Java, PHP 등)이 예고 없이 종료됨

## 확인한 내용

EC2 콘솔에서 시스템 로그 확인:

1. EC2 콘솔 → 인스턴스 선택 → Actions → Monitor and troubleshoot → Get system log
2. 로그에서 `Out of memory: kill process` 검색

인스턴스 재부팅 후 현재 메모리 상태 확인:

```bash
free -h
top -b -n 1 | head -20
ps aux --sort=-%mem | head -20
```

CloudWatch에서 메모리 사용량 추세 확인 (메모리 메트릭은 CloudWatch Agent 설치 필요).

## 원인

인스턴스의 물리 메모리(RAM)와 swap이 모두 고갈됨. Linux 커널의 OOM Killer가 메모리 회수를 위해 프로세스를 강제 종료함. 주요 원인:

- 현재 인스턴스 타입의 메모리가 워크로드에 비해 부족
- 애플리케이션 메모리 누수
- 트래픽 폭증으로 인한 프로세스 수 급증

## 해결 방법

**즉각적 조치:**

EBS 루트 볼륨 인스턴스인 경우:

```bash
# 메모리 집중 프로세스 확인 및 정리
ps aux --sort=-%mem | head -10
kill -9 <PID>
```

인스턴스 재시작 (EBS 백업 인스턴스):

EC2 콘솔 → Instance state → Stop → Start (재시작)

**근본 해결:**

1. 인스턴스 타입을 메모리가 더 많은 타입으로 변경 (예: t3.medium → t3.large)
2. swap 공간 추가:

```bash
sudo dd if=/dev/zero of=/swapfile bs=128M count=16
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile swap swap defaults 0 0' | sudo tee -a /etc/fstab
```

3. Auto Scaling 설정으로 트래픽 폭증 시 자동 스케일 아웃 구성

## 재발 방지

- CloudWatch Agent로 메모리 사용량 메트릭을 수집하고 임계값 알람(예: 80%) 설정
- 메모리 누수가 있는 애플리케이션은 정기적 재시작 스케줄 설정 (임시 조치)
- Auto Scaling Group에 인스턴스를 배치하여 트래픽 폭증 시 자동 확장
- 애플리케이션 메모리 프로파일링으로 누수 원인 분석 및 수정

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstances.html
