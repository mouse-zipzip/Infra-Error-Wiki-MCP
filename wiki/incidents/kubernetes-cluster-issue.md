# Kubernetes Cluster Issue

## 대표 증상

- `Node NotReady`
- `Kubelet stopped posting node status.`
- `The connection to the server :6443 was refused`
- `The connection to the server <apiserver>:6443 was refused - did you specify the right host or port?`
- `Unable to connect to the server: EOF`
- `dial tcp <ip>:6443: connect: connection refused`

- `kube-worker-1 NotReady <none> 1h v1.23.3`

---

## 원인

kubelet 프로세스 종료, 노드-control plane 네트워크 단절, API Server 크래시, etcd 손실 등

---

## 원인 유형

### Kubernetes API Server에 접근 불가 (control plane 장애)

증상:
- `The connection to the server <apiserver>:6443 was refused - did you specify the right host or port?`
- `Unable to connect to the server: EOF`
- `dial tcp <ip>:6443: connect: connection refused`

원인:
API Server에 접근 불가능한 주요 원인 **API Server VM/프로세스 크래시:** API Server 자체가 종료됨 **etcd(backing storage) 손실 또는 불가:** API Server가 etcd에 접근 못 하여 시작 실패 **네트워크 파티션:** 클라이언트와 control plane 사이 네트워크 단절 **인증서 만료:** API Server의 TLS 인증서 또는 kubeconfig의 클라이언트 인증서 만료

해결:
- `방법 1: API Server 프로세스 재시작`
- `방법 2: etcd 복구`
- `방법 3: 인증서 갱신 (kubeadm)`

요약:
- 원본: `raw/sources/k8s-api-server-unreachable.md`
- 상황: `kubectl get pods`, `kubectl get nodes` 등 모든 kubectl 명령이 실패
- 해결 요약: 방법 1: API Server 프로세스 재시작

---

### Kubernetes 노드가 NotReady 상태이고 kubelet이 상태를 보고하지 않음

증상:
- `kube-worker-1 NotReady <none> 1h v1.23.3`

원인:
- 노드 자체 다운 (전원 꺼짐, 크래시)
- `노드와 control plane 사이 네트워크 단절`
- `kubelet 프로세스 종료 또는 재시작 실패`
- `노드의 디스크/메모리 고갈로 kubelet이 강제 종료됨`

확인:
1. Ready condition의 status가 Unknown 또는 False 여부
2. Kubelet stopped posting node status. 메시지 존재 여부
3. node.kubernetes.io/unreachable taint 존재 여부

해결:
- 노드 자체 접근 가능 여부 확인
- `kubelet 재시작 (노드 접근 가능한 경우)`
- 노드 리소스 확인 (디스크/메모리)
- 네트워크 연결 확인
- 노드를 클러스터에서 제거하고 재등록 (최후 수단)

요약:
- 원본: `raw/sources/k8s-node-notready-kubelet-stopped.md`
- 상황: `kubectl get nodes` 결과에서 특정 노드만 `NotReady` 상태
- 해결 요약: 노드 자체 접근 가능 여부 확인

---

## 검색 태그

kubernetes, k8s, cluster, node, kubelet, apiserver, tls, certificate, port

---
