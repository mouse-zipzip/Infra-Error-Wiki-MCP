# Kubernetes 노드가 NotReady 상태이고 kubelet이 상태를 보고하지 않음

## 발생한 오류

```
NAME            STATUS     ROLES   AGE   VERSION
kube-worker-1   NotReady   <none>  1h    v1.23.3
```

`kubectl describe node <node-name>` 출력에서:

```
MemoryPressure   Unknown   NodeStatusUnknown   Kubelet stopped posting node status.
DiskPressure     Unknown   NodeStatusUnknown   Kubelet stopped posting node status.
PIDPressure      Unknown   NodeStatusUnknown   Kubelet stopped posting node status.
Ready            Unknown   NodeStatusUnknown   Kubelet stopped posting node status.
```

그리고 taint 확인 시:

```
node.kubernetes.io/unreachable:NoExecute
node.kubernetes.io/unreachable:NoSchedule
```

## 당시 상황

- `kubectl get nodes` 결과에서 특정 노드만 `NotReady` 상태
- 해당 노드에 스케줄링된 Pod가 `Pending` 또는 `Terminating` 상태로 전환됨
- 클러스터 전체는 동작하나 해당 노드의 Pod만 영향을 받음

## 확인한 내용

**노드 상태 확인:**

```bash
kubectl get nodes
kubectl describe node <node-name>
kubectl get node <node-name> -o yaml
```

**핵심 확인 포인트:**
- `Ready` condition의 status가 `Unknown` 또는 `False` 여부
- `Kubelet stopped posting node status.` 메시지 존재 여부
- `node.kubernetes.io/unreachable` taint 존재 여부

**노드에 직접 접속하여 kubelet 상태 확인 (가능한 경우):**

```bash
systemctl status kubelet
journalctl -u kubelet --since "30 minutes ago"
```

**Worker node 로그 확인:**

```bash
# systemd 기반
journalctl -u kubelet
# 파일 기반
cat /var/log/kubelet.log
```

## 원인

kubelet이 control plane(kube-apiserver)에 노드 상태를 더 이상 보고하지 못하는 상황. 원인 후보:

- 노드 자체 다운 (전원 꺼짐, 크래시)
- 노드와 control plane 사이 네트워크 단절
- kubelet 프로세스 종료 또는 재시작 실패
- 노드의 디스크/메모리 고갈로 kubelet이 강제 종료됨

## 해결 방법

**1. 노드 자체 접근 가능 여부 확인**

SSH로 노드에 접근 시도. 접근이 안 된다면 노드 다운 또는 네트워크 단절 가능성.

**2. kubelet 재시작 (노드 접근 가능한 경우)**

```bash
sudo systemctl restart kubelet
sudo systemctl status kubelet
```

**3. 노드 리소스 확인 (디스크/메모리)**

```bash
df -h
free -h
```

디스크 또는 메모리가 고갈된 경우 정리 후 kubelet 재시작.

**4. 네트워크 연결 확인**

노드에서 kube-apiserver로 연결 테스트:

```bash
curl -k https://<apiserver-ip>:6443/healthz
```

**5. 노드를 클러스터에서 제거하고 재등록 (최후 수단)**

```bash
kubectl drain <node-name> --ignore-daemonsets --delete-emptydir-data
kubectl delete node <node-name>
# 노드에서 kubeadm join 재실행
```

## 재발 방지

- 노드의 디스크/메모리 사용량을 CloudWatch 또는 Prometheus로 모니터링하고 임계값 알림 설정
- `Node Problem Detector`를 설치하여 kubelet 장애 조기 감지
- Replication Controller 또는 Deployment를 사용하여 노드 장애 시 다른 노드에서 자동으로 Pod 재시작되도록 구성
- control plane HA(고가용성) 구성으로 단일 노드 장애가 클러스터 전체에 미치는 영향 최소화

## 참고

- https://kubernetes.io/docs/tasks/debug/debug-cluster/
