# Kubernetes API Server에 접근 불가 (control plane 장애)

## 발생한 오류

```
The connection to the server <apiserver>:6443 was refused - did you specify the right host or port?
```

또는:

```
Unable to connect to the server: EOF
dial tcp <ip>:6443: connect: connection refused
```

`kubectl` 명령어가 모두 실패하고 클러스터에 어떠한 변경도 불가능한 상태.

## 당시 상황

- `kubectl get pods`, `kubectl get nodes` 등 모든 kubectl 명령이 실패
- 새로운 Pod, Service, Deployment 생성 불가
- 기존에 실행 중이던 Pod와 Service는 일반적으로 계속 동작함
- API Server VM이 재시작되었거나 프로세스가 크래시된 후 발생

## 확인한 내용

**kubectl 연결 가능 여부:**

```bash
kubectl cluster-info
kubectl get nodes
```

**API Server 프로세스 또는 Pod 상태 확인 (control plane 노드 접근 가능 시):**

```bash
# kubeadm 기반 클러스터 (static pod)
crictl ps | grep kube-apiserver
journalctl -u kubelet | tail -50

# 바이너리 직접 실행 환경
systemctl status kube-apiserver
cat /var/log/kube-apiserver.log | tail -100
```

**etcd 상태 확인:**

```bash
ETCDCTL_API=3 etcdctl endpoint health \
  --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt \
  --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key
```

## 원인

API Server에 접근 불가능한 주요 원인:

1. **API Server VM/프로세스 크래시:** API Server 자체가 종료됨
2. **etcd(backing storage) 손실 또는 불가:** API Server가 etcd에 접근 못 하여 시작 실패
3. **네트워크 파티션:** 클라이언트와 control plane 사이 네트워크 단절
4. **인증서 만료:** API Server의 TLS 인증서 또는 kubeconfig의 클라이언트 인증서 만료

## 해결 방법

**방법 1: API Server 프로세스 재시작**

kubeadm 기반:

```bash
# control plane 노드에서
sudo crictl rm -f $(sudo crictl ps -a | grep kube-apiserver | awk '{print $1}')
# kubelet이 자동으로 static pod를 재시작함
sudo systemctl restart kubelet
```

바이너리 실행:

```bash
sudo systemctl restart kube-apiserver
```

**방법 2: etcd 복구**

etcd가 응답하지 않는 경우:

```bash
sudo systemctl restart etcd
# 또는 etcd pod 재시작 (kubeadm 기반)
```

etcd 데이터가 손실된 경우 스냅샷에서 복구:

```bash
ETCDCTL_API=3 etcdctl snapshot restore /backup/etcd-snapshot.db \
  --data-dir=/var/lib/etcd-restore
```

**방법 3: 인증서 갱신 (kubeadm)**

```bash
sudo kubeadm certs renew all
sudo systemctl restart kubelet
```

## 재발 방지

- control plane 노드를 최소 3개로 구성하여 HA 확보 (단일 API Server 장애 대비)
- etcd 데이터의 주기적 스냅샷 백업 설정 (EBS 또는 GCE PD 스냅샷 포함)
- 인증서 만료일 모니터링: `kubeadm certs check-expiration`
- IaaS의 자동 VM 재시작(Auto Recovery) 기능 활성화

## 참고

- https://kubernetes.io/docs/tasks/debug/debug-cluster/
- https://kubernetes.io/docs/tasks/administer-cluster/configure-upgrade-etcd/
