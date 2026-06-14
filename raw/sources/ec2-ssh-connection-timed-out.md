# EC2 Linux 인스턴스 SSH 연결 타임아웃

## 발생한 오류

```
Network error: Connection timed out
```

또는:

```
Error connecting to [instance], reason: -> Connection timed out: connect
ssh: connect to host ec2-xx-xx-xx-xx.compute-1.amazonaws.com port 22: Connection timed out
```

SSH 클라이언트가 일정 시간 대기하다 타임아웃으로 연결 실패.

## 당시 상황

- EC2 인스턴스를 새로 시작하거나, 잠시 접속하지 않다가 재접속할 때 발생
- 다른 네트워크(집, 회사, 모바일 핫스팟 등)로 변경한 후 접속 시 발생
- 인스턴스는 running 상태이고 상태 체크는 통과하고 있음

## 확인한 내용

**1. 보안 그룹(Security Group) 인바운드 규칙 확인**

EC2 콘솔 → 인스턴스 → Security 탭 → Inbound rules에서 포트 22(SSH) 허용 규칙 확인:

- Source가 현재 접속하는 IP 주소를 포함하는지 확인
- `0.0.0.0/0` (전체 허용) 또는 현재 IP의 `/32` 규칙이 있어야 함

현재 공인 IP 확인:

```bash
curl ifconfig.me
```

**2. 라우팅 테이블 확인**

EC2 콘솔 → 인스턴스 → Networking 탭 → Subnet ID 클릭 → Route table 탭:
- `0.0.0.0/0` 목적지에 Internet Gateway(igw-xxx)가 연결되어 있는지 확인

**3. 네트워크 ACL 확인**

VPC 콘솔 → Subnets → Network ACL 탭:
- 인바운드: 포트 22 허용 여부
- 아웃바운드: 에페메랄 포트(1024-65535) 허용 여부

**4. 퍼블릭 IP 확인**

인스턴스에 퍼블릭 IPv4 주소가 없는 경우 인터넷에서 직접 접근 불가.

**5. 인스턴스 CPU 부하 확인**

CloudWatch → EC2 → 해당 인스턴스 → CPUUtilization 메트릭

## 원인

타임아웃이 발생하는 주요 원인:

- 보안 그룹에 현재 IP에서 포트 22로의 인바운드 규칙 없음
- 서브넷 라우팅 테이블에 Internet Gateway가 없어 인터넷 통신 불가
- 네트워크 ACL이 SSH 트래픽을 차단
- 인스턴스에 퍼블릭 IP가 없음
- 인스턴스 CPU 과부하로 SSH 세션 거부

## 해결 방법

**보안 그룹에 인바운드 규칙 추가:**

EC2 콘솔 → Security Groups → 해당 보안 그룹 → Inbound rules → Edit inbound rules:

```
Type: SSH
Protocol: TCP
Port: 22
Source: My IP (또는 접속 IP를 CIDR로 입력)
```

**서브넷에 Internet Gateway 라우트 추가:**

VPC 콘솔 → Route Tables → 서브넷 라우팅 테이블 → Routes → Edit routes:

```
Destination: 0.0.0.0/0
Target: igw-xxxxxxxxx (Internet Gateway)
```

**Elastic IP 할당 (퍼블릭 IP가 없는 경우):**

EC2 콘솔 → Elastic IPs → Allocate Elastic IP → 인스턴스에 연결(Associate)

## 재발 방지

- 동적 IP를 사용하는 환경(집, 카페 등)에서 접속할 때는 보안 그룹 Source를 단일 IP 대신 IP 대역으로 설정하거나, 접속 전 보안 그룹 규칙을 업데이트하는 스크립트 사용
- 인스턴스는 기본적으로 Elastic IP 또는 퍼블릭 서브넷에 배치하여 연결 가능성 확보
- bastion host(jump server)를 사용하여 직접 SSH 노출을 줄임

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstancesConnecting.html
