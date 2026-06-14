#!/usr/bin/env python3
"""Local wiki tool server for Infra Error Archive."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WIKI_DIR = ROOT / "wiki"
RAW_DIR = ROOT / "raw" / "sources"
INDEX_PATH = WIKI_DIR / "index.json"
LOG_PATH = ROOT / "logs" / "agent-actions.log"
CATEGORIES = ("incidents",)
REQUIRED_PAGE_SECTIONS = ("대표 증상", "원인", "원인 유형", "검색 태그")
LOW_SIGNAL_SEARCH_TOKENS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "daemon",
    "docker",
    "error",
    "failed",
    "failure",
    "for",
    "from",
    "get",
    "http",
    "https",
    "in",
    "is",
    "issue",
    "message",
    "of",
    "on",
    "or",
    "post",
    "problem",
    "response",
    "the",
    "to",
    "was",
    "were",
    "with",
}

SECTION_ALIASES = {
    "발생한 오류": "error",
    "오류": "error",
    "에러": "error",
    "observed error": "error",
    "error": "error",
    "당시 상황": "context",
    "상황": "context",
    "context": "context",
    "확인한 내용": "checked",
    "확인 내용": "checked",
    "raw evidence / notes": "checked",
    "notes": "checked",
    "원인": "cause",
    "cause": "cause",
    "해결 방법": "resolution",
    "해결": "resolution",
    "resolution": "resolution",
    "재발 방지": "prevention",
    "예방": "prevention",
    "참고": "reference",
    "reference": "reference",
}

PROBLEM_RULES = [
    {
        "slug": "port-binding-conflict",
        "title": "Port Binding Conflict",
        "category": "incidents",
        "keywords": [
            "port is already allocated",
            "address already in use",
            "bind failed",
            "eaddrinuse",
            "listen tcp",
            "already in use",
        ],
        "tags": ["port", "bind", "networking", "docker"],
        "symptoms": ["port is already allocated", "address already in use", "bind failed", "EADDRINUSE"],
        "problem": "Host port가 이미 점유되어 service 또는 container가 시작되지 않는 문제",
        "contexts": ["Docker container 실행", "Spring Boot local server 실행", "DB container 실행"],
        "cause": "Host의 특정 port는 동시에 하나의 process만 bind할 수 없습니다.",
        "checks": [
            "에러 메시지에서 port 번호를 확인한다.",
            "host에서 해당 port를 점유 중인 process를 찾는다.",
            "기존 process를 종료할지, host port mapping을 바꿀지 결정한다.",
        ],
        "strategies": ["기존 process 종료", "기존 container 중지", "host port 변경", "개발용 port 규칙 정리"],
        "concepts": ["Port Binding", "Docker Port Mapping"],
    },
    {
        "slug": "docker-volume-mount-runtime-error",
        "title": "Docker 볼륨 마운트 시 런타임 오류 또는 파일 접근 실패",
        "category": "incidents",
        "keywords": [
            "mounts denied",
            "not shared from the host",
            "docker volume mount",
            "volume mount",
            "file sharing",
            "shared folders",
            "open /app/data",
        ],
        "tags": ["docker", "volume", "mount", "file-sharing", "container"],
        "symptoms": [
            "Error response from daemon: Mounts denied:",
            "The path is not shared from the host and is not known to Docker.",
            "Permission denied",
            "open /app/data/file.txt: no such file or directory",
        ],
        "problem": "Docker container가 host 경로를 volume으로 mount했지만 Docker Desktop 파일 공유 설정이나 host path 조건이 맞지 않아 파일 접근에 실패하는 문제",
        "contexts": [
            "docker run -v 또는 docker compose volume mount 사용",
            "프로젝트 경로가 Docker Desktop 공유 경로 밖에 있음",
            "container 내부에서 mounted directory read/write 실패",
        ],
        "cause": "Docker Desktop은 허용된 host 경로만 container에 공유하므로, 공유 목록에 없는 경로나 권한이 맞지 않는 경로를 mount하면 daemon 또는 container 내부 파일 접근 오류가 발생합니다.",
        "checks": [
            "에러 메시지에 Mounts denied 또는 not shared from the host가 있는지 확인한다.",
            "Docker Desktop Settings > Resources > File sharing에 host path가 등록되어 있는지 확인한다.",
            "container 내부에서 mount 대상 경로가 존재하고 read/write 가능한지 확인한다.",
            "host path가 홈 디렉토리 또는 공유 허용 경로 아래에 있는지 확인한다.",
        ],
        "strategies": [
            "Docker Desktop 파일 공유 설정에 host path 추가",
            "프로젝트를 Docker가 기본 공유하는 홈 디렉토리 아래로 이동",
            "host path mount 대신 Docker named volume 사용",
            "container 내부 경로와 권한 재확인",
        ],
        "concepts": ["Docker Volume Mount", "Docker Desktop File Sharing"],
    },
    {
        "slug": "ec2-ssh-connection-failure",
        "title": "EC2 SSH Connection Failure",
        "category": "incidents",
        "keywords": [
            "permission denied (publickey)",
            "host key verification failed",
            "unprotected private key file",
            "lost my private key",
            "known_hosts",
            "authorized_keys",
            "ssh connection timed out",
            "network error: connection timed out",
            "bad permissions: ignore key",
        ],
        "tags": ["ec2", "ssh", "key", "connection", "publickey"],
        "symptoms": [
            "Permission denied (publickey)",
            "Network error: Connection timed out",
            "Host key verification failed",
            "WARNING: UNPROTECTED PRIVATE KEY FILE!",
        ],
        "problem": "EC2 Linux 인스턴스에 SSH 연결이 실패하거나 키 인증 오류가 발생하는 문제",
        "contexts": [
            "SSH 키 파일(.pem) 권한 문제",
            "보안 그룹에 포트 22 인바운드 규칙 없음",
            "known_hosts의 호스트 키 불일치",
            "개인 키 분실로 인스턴스 접근 불가",
        ],
        "cause": "SSH 공개 키 인증 실패, 키 파일 권한 설정 오류, 보안 그룹 누락, known_hosts 불일치 등 다양한 원인이 있습니다.",
        "checks": [
            "AMI별 기본 사용자명 확인 (Amazon Linux: ec2-user, Ubuntu: ubuntu)",
            "키 파일 권한 확인: chmod 400 key.pem",
            "보안 그룹에 포트 22 인바운드 허용 규칙 존재 여부",
            "known_hosts에 저장된 호스트 키와 현재 서버 키 일치 여부",
            "인스턴스 퍼블릭 IP 및 Elastic IP 할당 여부",
        ],
        "strategies": [
            "chmod 400 key.pem으로 키 파일 권한 수정",
            "보안 그룹에 SSH(22) 인바운드 규칙 추가",
            "ssh-keygen -R <host>로 known_hosts 항목 제거",
            "임시 인스턴스로 authorized_keys 교체 (키 분실 시)",
        ],
        "concepts": ["EC2 Key Pair", "SSH Public Key Authentication", "Security Group"],
    },
    {
        "slug": "ec2-instance-system-error",
        "title": "EC2 Instance System Error",
        "category": "incidents",
        "keywords": [
            "out of memory: kill process",
            "i/o error, dev",
            "end_request: i/o error",
            "fatal: kernel too old",
            "could not load /lib/modules",
            "unable to load selinux",
            "selinux policy",
            "mac address than expected",
            "fsck",
            "e2label",
            "xfs_admin",
            "booting from wrong volume",
            "wrong volume",
            "fstab",
        ],
        "tags": ["ec2", "kernel", "filesystem", "memory", "selinux", "volume", "boot"],
        "symptoms": [
            "Out of memory: kill process",
            "I/O error, dev sde",
            "FATAL: kernel too old",
            "Unable to load SELinux Policy. Machine is in enforcing mode. Halting now.",
            "Device eth0 has different MAC address than expected, ignoring.",
        ],
        "problem": "EC2 Linux 인스턴스가 시스템 레벨 오류로 인해 부팅에 실패하거나 상태 체크를 통과하지 못하는 문제",
        "contexts": [
            "인스턴스 상태 체크(System/Instance status check) 실패",
            "재부팅 후 SSH 연결 불가",
            "다른 볼륨을 연결한 후 잘못된 볼륨으로 부팅",
            "커널 업그레이드 또는 AMI 변경 후 부팅 실패",
        ],
        "cause": "메모리 고갈, 블록 디바이스 I/O 오류, 커널-AMI 불일치, /etc/fstab 설정 오류, SELinux 설정 오류, MAC 주소 하드코딩, 볼륨 label 충돌 등 다양한 시스템 레벨 원인이 있습니다.",
        "checks": [
            "EC2 콘솔 → Actions → Monitor and troubleshoot → Get system log에서 오류 확인",
            "Out of memory 키워드: 메모리 부족",
            "I/O error 키워드: EBS 볼륨 또는 물리 디스크 장애",
            "FATAL: kernel too old: 커널-AMI 불일치",
            "fsck 오류: /etc/fstab에 없는 디바이스 참조",
            "SELinux: enforcing 모드이지만 policy 미설치",
            "MAC address: AMI에 하드코딩된 네트워크 설정",
            "볼륨 label 충돌: sudo e2label /dev/xvda1 vs /dev/xvdf1",
        ],
        "strategies": [
            "인스턴스 재시작 (EBS 기반)",
            "swap 파티션 추가로 메모리 부족 완화",
            "임시 인스턴스로 /etc/fstab 수정 (nofail 옵션 추가)",
            "임시 인스턴스로 SELinux 설정을 permissive로 변경",
            "볼륨 label 변경: sudo e2label /dev/xvdf1 old/",
            "네트워크 설정에서 하드코딩된 MAC 주소 제거",
        ],
        "concepts": ["EC2 Status Check", "EBS Volume", "Linux Boot Process", "fsck"],
    },
    {
        "slug": "docker-desktop-startup-issue",
        "title": "Docker Desktop 시작/표시 오류",
        "category": "incidents",
        "keywords": [
            "docker desktop - access denied",
            "docker-users",
            "hcs_e_hyperv_not_installed",
            "hyperv_not_installed",
            "disablehardwareacceleration",
            "bcdedit /set hypervisorlaunchtype",
            "virtual machine platform",
            "wsl/service",
        ],
        "tags": ["docker", "desktop", "windows", "hyper-v", "virtualization", "access-denied"],
        "symptoms": [
            "Docker Desktop - Access Denied",
            "Wsl/Service/RegisterDistro/CreateVm/HCS/HCS_E_HYPERV_NOT_INSTALLED",
            "Docker Desktop UI 녹색/왜곡/아티팩트",
        ],
        "problem": "Docker Desktop이 실행되지 않거나 UI에 시각적 문제가 발생하는 오류",
        "contexts": [
            "Docker Desktop 설치 후 처음 실행",
            "새 Windows 사용자 계정으로 로그인 후",
            "특정 GPU 드라이버 환경",
            "Hyper-V 또는 WSL2가 비활성화된 Windows 환경",
        ],
        "cause": "docker-users 그룹 미포함, Windows Hyper-V/WSL2 비활성화, BIOS 가상화 비활성화, GPU 하드웨어 가속 충돌 등",
        "checks": [
            "현재 사용자가 docker-users 그룹에 속하는지 확인: net localgroup docker-users",
            "작업 관리자 → 성능 → CPU → 가상화 사용 여부 확인",
            "wsl -l -v로 WSL2 상태 확인",
            "Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V로 Hyper-V 확인",
            "UI 문제: settings-store.json에서 disableHardwareAcceleration 설정",
        ],
        "strategies": [
            "net localgroup docker-users <사용자명> /add 후 재로그인",
            "BIOS에서 Intel VT-x 또는 AMD-V 가상화 활성화",
            "WSL2/Hyper-V Windows 기능 설치 및 bcdedit /set hypervisorlaunchtype auto",
            "settings-store.json에 disableHardwareAcceleration: true 추가",
        ],
        "concepts": ["Docker Users Group", "Hyper-V", "WSL2", "Hardware Acceleration"],
    },
    {
        "slug": "github-actions-workflow-issue",
        "title": "GitHub Actions Workflow Issue",
        "category": "incidents",
        "keywords": [
            "github actions",
            "workflow",
            "runs-on",
            "always()",
            "runner",
            "pull_request",
            "workflow_dispatch",
            "skip ci",
            "runner-images",
        ],
        "tags": ["github", "github-actions", "workflow", "runner", "ci-cd"],
        "symptoms": [
            "워크플로우가 트리거되지 않음",
            "취소(Cancel) 후에도 잡이 계속 실행됨",
            "의도하지 않은 러너에서 잡이 실행됨",
        ],
        "problem": "GitHub Actions 워크플로우가 예상대로 실행되지 않거나 제어되지 않는 문제",
        "contexts": [
            "push 또는 pull_request 후 워크플로우 미실행",
            "워크플로우 취소 요청 후에도 잡이 계속 실행",
            "self-hosted runner 환경에서 잡이 예상 외 러너에 할당",
        ],
        "cause": "워크플로우 비활성화, on: 조건 불일치, always() 함수의 취소 무시, runner label 충돌 등",
        "checks": [
            "Actions 탭에서 워크플로우 활성화 여부 확인",
            "on: 섹션의 브랜치/이벤트 조건과 현재 상황 일치 여부",
            "커밋 메시지에 [skip ci] 포함 여부 확인",
            "PR에 머지 충돌 여부 확인",
            "if: 조건에 always() 사용 여부 확인",
            "self-hosted runner label이 GitHub-hosted preset label과 중복 여부 확인",
        ],
        "strategies": [
            "워크플로우 재활성화",
            "on: 조건 수정 (브랜치, 이벤트 타입)",
            "always() → !cancelled() 로 변경",
            "runner label을 고유한 이름으로 변경 (예: self-hosted-prod)",
        ],
        "concepts": ["GitHub Actions Events", "Runner Labels", "Job Conditions"],
    },
    {
        "slug": "kubernetes-cluster-issue",
        "title": "Kubernetes Cluster Issue",
        "category": "incidents",
        "keywords": [
            "kubectl",
            "kubelet",
            "kube-apiserver",
            "notready",
            "kubelet stopped posting",
            "node.kubernetes.io/unreachable",
            "etcd",
            "control plane",
            "kubectl get nodes",
        ],
        "tags": ["kubernetes", "k8s", "cluster", "node", "kubelet", "apiserver"],
        "symptoms": [
            "Node NotReady",
            "Kubelet stopped posting node status.",
            "The connection to the server :6443 was refused",
        ],
        "problem": "Kubernetes 클러스터 노드가 NotReady 상태이거나 API Server에 접근이 불가능한 문제",
        "contexts": [
            "kubectl get nodes에서 특정 노드가 NotReady",
            "모든 kubectl 명령이 실패",
            "노드 네트워크 단절 또는 kubelet 프로세스 종료",
        ],
        "cause": "kubelet 프로세스 종료, 노드-control plane 네트워크 단절, API Server 크래시, etcd 손실 등",
        "checks": [
            "kubectl get nodes로 전체 노드 상태 확인",
            "kubectl describe node <name>에서 Conditions와 Taints 확인",
            "systemctl status kubelet로 kubelet 상태 확인",
            "curl -k https://<apiserver>:6443/healthz로 API Server 응답 확인",
            "/var/log/kube-apiserver.log 및 /var/log/kubelet.log 확인",
        ],
        "strategies": [
            "systemctl restart kubelet",
            "kubeadm certs renew all로 인증서 갱신",
            "etcd 스냅샷에서 복구",
            "kubectl drain 후 노드 재등록",
        ],
        "concepts": ["Kubernetes Control Plane", "kubelet", "etcd"],
    },
    {
        "slug": "reverse-proxy-upstream-failure",
        "title": "Reverse Proxy Upstream Failure",
        "category": "incidents",
        "keywords": ["502", "bad gateway", "upstream", "proxy_pass", "nginx upstream"],
        "tags": ["nginx", "proxy", "upstream", "502"],
        "symptoms": ["502 Bad Gateway", "upstream connection refused", "connect() failed"],
        "problem": "Reverse proxy가 upstream application에 연결하지 못해 요청 처리가 실패하는 문제",
        "contexts": ["Nginx reverse proxy 구성", "Spring Boot 또는 API server 재시작", "Docker network 변경"],
        "cause": "Proxy 설정의 upstream 주소 또는 port와 실제 application 실행 상태가 일치하지 않을 수 있습니다.",
        "checks": [
            "upstream application이 실행 중인지 확인한다.",
            "proxy_pass 주소와 실제 application port가 일치하는지 확인한다.",
            "proxy host에서 upstream URL로 직접 요청을 보내 본다.",
        ],
        "strategies": ["upstream application 재시작", "proxy_pass 주소 수정", "container network와 port mapping 점검"],
        "concepts": ["Reverse Proxy", "Nginx Upstream"],
    },
    {
        "slug": "docker-private-registry-tls-configuration-failure",
        "title": "Docker Private Registry TLS Configuration Failure",
        "category": "incidents",
        "keywords": [
            "malformed http response",
            "\\x15\\x03\\x01",
            "private registry",
            "insecure-registries",
            "certs.d",
            "self-signed",
            "ca.crt",
        ],
        "tags": ["docker", "registry", "tls", "certificate", "insecure-registry"],
        "symptoms": [
            'malformed HTTP response "\\x15\\x03\\x01..."',
            "private registry pull/push failure",
            "Docker registry TLS handshake mismatch",
        ],
        "problem": "Docker private registry 접속 시 HTTP/HTTPS 설정 또는 TLS 인증서 신뢰 설정이 맞지 않아 push/pull이 실패하는 문제",
        "contexts": [
            "self-signed 인증서를 사용하는 private registry",
            "insecure registry로 접근해야 하는 개발/테스트 환경",
        ],
        "cause": "Docker client와 registry server가 기대하는 HTTP/HTTPS 프로토콜 또는 인증서 신뢰 설정이 일치하지 않습니다.",
        "checks": [
            "registry 주소와 port가 HTTP용인지 HTTPS용인지 확인한다.",
            "Docker daemon의 insecure-registries 설정을 확인한다.",
            "/etc/docker/certs.d/<registry-host>:<port>/ca.crt 등록 여부를 확인한다.",
            "설정 변경 후 Docker daemon을 재시작했는지 확인한다.",
        ],
        "strategies": [
            "self-signed CA 인증서를 Docker certs.d 경로에 등록",
            "개발/테스트 환경에서는 insecure-registries 설정 사용",
            "운영 환경에서는 공인 CA 또는 올바른 TLS 인증서로 registry 구성",
        ],
        "concepts": ["Docker Registry", "TLS Certificate", "Insecure Registry"],
    },
]


def now_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).isoformat(timespec="seconds")


def today_kst() -> str:
    return datetime.now(timezone(timedelta(hours=9))).date().isoformat()


def log_action(actor: str, action: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{now_kst()}] {actor} {action}\n")


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", title.lower()).strip("-")
    return slug or "untitled"


def read_index() -> list[dict[str, Any]]:
    if not INDEX_PATH.exists():
        return []
    with INDEX_PATH.open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError("wiki/index.json must contain a list")
    return data


def write_index(entries: list[dict[str, Any]]) -> None:
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    normalized = sorted(entries, key=lambda item: (item["category"], item["slug"]))
    with INDEX_PATH.open("w", encoding="utf-8") as handle:
        json.dump(normalized, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def page_path(category: str, slug: str) -> Path:
    if category not in CATEGORIES:
        raise ValueError(f"Unsupported category: {category}")
    return WIKI_DIR / category / f"{slug}.md"


def rel_project_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_title(markdown: str, fallback: str) -> str:
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def unique_list(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        clean = str(value).strip()
        if clean and clean not in result:
            result.append(clean)
    return result


def extract_tags(text: str) -> list[str]:
    vocabulary = {
        "nginx": "nginx",
        "502": "502",
        "bad gateway": "bad-gateway",
        "reverse proxy": "reverse-proxy",
        "proxy": "proxy",
        "upstream": "upstream",
        "spring": "spring-boot",
        "boot": "spring-boot",
        "ec2": "ec2",
        "docker": "docker",
        "desktop": "desktop",
        "wsl": "wsl2",
        "wsl2": "wsl2",
        "gpu": "gpu",
        "hardware acceleration": "hardware-acceleration",
        "hardware-acceleration": "hardware-acceleration",
        "access denied": "access-denied",
        "registry": "registry",
        "tls": "tls",
        "certificate": "certificate",
        "cert": "certificate",
        "self-signed": "self-signed",
        "insecure": "insecure-registry",
        "port": "port",
        "bind": "bind",
        "container": "container",
        "firewall": "firewall",
        "eaddrinuse": "eaddrinuse",
    }
    lowered = text.lower()
    tags: list[str] = []
    for needle, tag in vocabulary.items():
        if needle in lowered:
            tags.append(tag)
    return unique_list(tags)[:8]


def parse_markdown_sections(raw: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {"body": []}
    current = "body"
    for line in raw.splitlines():
        match = re.match(r"^#{2,6}\s+(.+?)\s*$", line)
        if match:
            current = match.group(1).strip()
            sections.setdefault(current, [])
            continue
        if not line.startswith("# "):
            sections.setdefault(current, []).append(line)
    return {key: "\n".join(value).strip() for key, value in sections.items() if "\n".join(value).strip()}


def normalize_raw_record(raw: str, source_path: Path) -> dict[str, Any]:
    title = extract_title(raw, source_path.stem.replace("-", " ").title())
    sections = parse_markdown_sections(raw)
    normalized_sections: dict[str, str] = {}
    for heading, content in sections.items():
        alias = SECTION_ALIASES.get(heading.strip().lower())
        if alias:
            normalized_sections[alias] = content

    record = {
        "title": title.replace("Raw Source: ", "").replace("Raw Debug Log: ", "").strip(),
        "source_path": rel_project_path(source_path),
        "error": normalized_sections.get("error", ""),
        "context": normalized_sections.get("context", ""),
        "checked": normalized_sections.get("checked", ""),
        "cause": normalized_sections.get("cause", ""),
        "resolution": normalized_sections.get("resolution", ""),
        "prevention": normalized_sections.get("prevention", ""),
        "reference": normalized_sections.get("reference", ""),
        "raw": raw.strip(),
    }
    if not record["error"]:
        record["error"] = first_nonempty_line(raw)
    return record


def first_nonempty_line(text: str) -> str:
    for line in text.splitlines():
        clean = line.strip()
        if clean and not clean.startswith("#"):
            return clean
    return ""


def infer_problem_type(record: dict[str, Any]) -> dict[str, Any]:
    haystack = " ".join(str(record.get(key, "")) for key in ("title", "error", "context", "checked", "cause", "resolution", "raw")).lower()
    for rule in PROBLEM_RULES:
        if any(keyword in haystack for keyword in rule["keywords"]):
            return dict(rule)

    tags = extract_tags(haystack)
    title = record["title"] or "Unclassified Infrastructure Error"
    return {
        "slug": slugify(title),
        "title": title,
        "category": "incidents",
        "tags": tags or ["incident"],
        "symptoms": unique_list([extract_error_summary(record.get("error", ""))])[:4],
        "problem": "아직 반복 패턴이 충분히 쌓이지 않은 인프라 오류 사건",
        "contexts": unique_list([one_line(record.get("context", ""), 120)])[:4],
        "cause": record.get("cause") or "원인 패턴을 추가로 확인해야 합니다.",
        "checks": extract_check_steps(record.get("checked", "")) or ["에러 메시지와 발생 위치를 확인한다.", "관련 process, port, proxy, network 설정을 점검한다.", "해결 후 raw 사건 기록을 보강한다."],
        "strategies": resolution_summaries(record.get("resolution", "")) or ["원인 확인 후 해결 전략을 문서에 보강"],
        "concepts": [],
    }


def find_related_problem_page(problem: dict[str, Any]) -> dict[str, Any] | None:
    for entry in read_index():
        if entry.get("slug") == problem["slug"]:
            return entry
    return None


def bullet_list(values: list[str]) -> str:
    values = unique_list(values)
    return "\n".join(format_list_item(item) for item in values if item)


def numbered_list(values: list[str]) -> str:
    return "\n".join(f"{index}. {value}" for index, value in enumerate(unique_list(values), start=1))


def looks_like_error_token(value: str) -> bool:
    if "\n" in value or "```" in value:
        return False
    if "`" in value:
        return False
    return bool(re.search(r"[A-Z_]{3,}|\d{3}|failed|error|allocated|refused|tcp|:", value, re.I))


def format_list_item(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if "\n" not in value:
        return f"- `{value}`" if looks_like_error_token(value) else f"- {value}"
    indented = "\n".join(f"  {line}" if line else "" for line in value.splitlines())
    return f"- {indented}"


def context_summary(value: str) -> str:
    """Context에서 첫 번째 의미 있는 한 줄 추출."""
    for line in value.splitlines():
        clean = re.sub(r"^\s*[-*]\s+", "", line).strip()
        if clean and len(clean) > 10:
            return one_line(clean, limit=150)
    return one_line(value, limit=150)


def case_block(record: dict[str, Any]) -> str:
    lines = [f"- 원본: `{record['source_path']}`"]
    if record.get("context"):
        lines.append(f"- 상황: {context_summary(record['context'])}")
    strategies = resolution_summaries(record.get("resolution", ""))
    if strategies:
        lines.append(f"- 해결 요약: {one_line(strategies[0])}")
    return "\n".join(lines)


def representative_case_title(record: dict[str, Any]) -> str:
    title = record.get("title", "").strip()
    if title:
        return re.sub(r"\s*\((Windows|Linux|Mac|macOS)\)\s*$", "", title).strip()
    error_summary = extract_error_summary(record.get("error", ""))
    return error_summary or "분류되지 않은 사례"


def representative_page_title(problem: dict[str, Any], record: dict[str, Any]) -> str:
    if problem.get("slug") == slugify(record.get("title", "")):
        return representative_case_title(record)
    return problem.get("title") or representative_case_title(record)


def representative_symptoms(record: dict[str, Any], fallback: list[str] | None = None) -> list[str]:
    values: list[str] = []
    summary = extract_error_summary(record.get("error", ""))
    if summary:
        values.append(summary)
    values.extend(extract_error_lines(record.get("error", "")))
    values.extend(markdown_list_items(record.get("error", "")))
    if fallback:
        values.extend(fallback)
    return unique_list(values)[:6]


def extract_error_lines(value: str) -> list[str]:
    keywords = (
        "i/o error", "buffer i/o error", "end_request", "permission denied",
        "host key verification failed", "unprotected private key", "notready",
        "fatal", "unable", "failed", "refused", "timeout", "out of memory",
    )
    lines: list[str] = []
    in_code = False
    for line in value.splitlines():
        stripped = strip_markdown_marker(line)
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        low = stripped.lower()
        if stripped and (in_code or any(keyword in low for keyword in keywords)):
            if any(keyword in low for keyword in keywords):
                lines.append(one_line(stripped, limit=180))
    return unique_list(lines)[:4]


def markdown_table_rows(value: str) -> list[str]:
    table_lines = [line.strip() for line in value.splitlines() if line.strip().startswith("|") and line.strip().endswith("|")]
    data_lines = [line for line in table_lines if not re.match(r"^\|[\s\-|:]+\|$", line)]
    if len(data_lines) < 2:
        return []

    rows = [
        [cell.strip() for cell in line.strip("|").split("|")]
        for line in data_lines
    ]
    headers = rows[0]
    result: list[str] = []
    for row in rows[1:]:
        if not any(row):
            continue
        if len(headers) >= 2 and len(row) >= 2:
            result.append(f"{row[0]}: {row[1]}")
        else:
            result.append(" - ".join(cell for cell in row if cell))
    return unique_list(result)


def cause_summary(value: str) -> str:
    table_items = markdown_table_rows(value)
    if table_items:
        return bullet_list(table_items)

    list_items = markdown_list_items(value)
    if len(list_items) > 1:
        return bullet_list(list_items)

    lines: list[str] = []
    in_code = False
    for line in value.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            continue
        clean = strip_markdown_marker(stripped)
        if clean:
            lines.append(clean)
    summary = concise_cause_text(lines)
    inline_items = split_inline_list(summary)
    if len(inline_items) > 1:
        return bullet_list(inline_items)
    return summary


def concise_cause_text(lines: list[str]) -> str:
    text = " ".join(lines)
    sentences = split_sentences(text)
    if not sentences:
        return one_line(text, limit=180)

    cause_keywords = (
        "because", "due to", "caused by", "mismatch", "misconfiguration",
        "일치하지", "맞지", "충돌", "누락", "없", "실패", "문제",
        "접근", "등록", "설정", "인증서", "프로토콜", "HTTP", "HTTPS", "TLS",
    )
    selected: list[str] = []
    for sentence in sentences:
        if any(keyword.lower() in sentence.lower() for keyword in cause_keywords):
            selected.append(sentence)
            break
    if not selected:
        selected.append(sentences[0])

    if len(selected[0]) < 80:
        for sentence in sentences:
            if sentence in selected:
                continue
            if len(" ".join([*selected, sentence])) <= 140:
                selected.append(sentence)
            break

    return one_line(" ".join(selected), limit=140)


def split_sentences(value: str) -> list[str]:
    clean = re.sub(r"\s+", " ", value).strip()
    if not clean:
        return []
    parts = re.split(r"(?<=[.!?。！？])\s+|(?<=[다요음됨함함다])\.\s*", clean)
    sentences = [part.strip() for part in parts if part.strip()]
    return sentences or [clean]


def split_inline_list(value: str) -> list[str]:
    parts = [part.strip(" :-") for part in re.split(r"\s+-\s+", value) if part.strip(" :-")]
    if len(parts) <= 1:
        return []
    head = parts[0]
    tail = parts[1:]
    if len(head) < 80:
        return [f"{head}: {tail[0]}", *tail[1:]]
    return parts


def cause_type_block(record: dict[str, Any]) -> str:
    title = representative_case_title(record)
    symptoms = representative_symptoms(record)
    checks = extract_check_steps(record.get("checked", ""))
    strategies = resolution_summaries(record.get("resolution", ""))
    lines = [f"### {title}", ""]
    if symptoms:
        lines.extend(["증상:", bullet_list(symptoms), ""])
    if record.get("cause"):
        lines.extend(["원인:", cause_summary(record["cause"]), ""])
    if checks:
        lines.extend(["확인:", numbered_list(checks), ""])
    if strategies:
        lines.extend(["해결:", bullet_list(strategies), ""])
    lines.extend(["요약:", case_block(record)])
    return "\n".join(lines).strip()


def one_line(value: str, limit: int = 180) -> str:
    clean = re.sub(r"\s+", " ", value).strip()
    return clean[: limit - 1] + "…" if len(clean) > limit else clean


def indent_block(value: str, spaces: int = 2) -> str:
    prefix = " " * spaces
    return "\n".join(f"{prefix}{line}" if line else "" for line in value.strip().splitlines())


def extract_check_steps(checked: str) -> list[str]:
    steps: list[str] = []
    in_code = False
    for line in checked.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code or not stripped:
            continue
        # 번호 목록: "1. 설명"
        m = re.match(r"^\d+\.\s+(.+)$", stripped)
        if m:
            clean = strip_markdown_marker(m.group(1))
            if clean and len(clean) < 120:
                steps.append(clean)
            continue
        # 백틱이 포함된 설명 줄 (코드 언급 있는 체크 항목)
        if "`" in stripped and not stripped.startswith("#") and len(stripped) > 8:
            clean = re.sub(r"`([^`]+)`", r"\1", stripped)
            clean = strip_markdown_marker(clean)
            clean = re.sub(r"\s+", " ", clean)
            if clean and len(clean) < 120:
                steps.append(clean)
    return unique_list(steps)[:5]


def strip_markdown_marker(value: str) -> str:
    clean = value.strip()
    clean = re.sub(r"^\s*[-*]\s+", "", clean)
    clean = re.sub(r"^\s*\d+\.\s+", "", clean)
    clean = re.sub(r"^`([^`]+)`$", r"\1", clean)
    clean = re.sub(r"^\*\*(.+?)\*\*$", r"\1", clean)
    return clean.strip().rstrip(":").strip()


def extract_error_summary(value: str) -> str:
    in_code = False
    code_lines: list[str] = []
    text_lines: list[str] = []
    for line in value.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            # 명령어 줄($, #) 및 언어 태그 제외
            if stripped and stripped not in {"bash", "json", "powershell", "text"} and not re.match(r"^\[?\S+@\S+\s+\S+\]?\$", stripped) and not stripped.startswith(("$ ", "# ", "> ")):
                code_lines.append(stripped)
        else:
            clean = strip_markdown_marker(line)
            if clean and clean not in {"bash", "json"}:
                text_lines.append(clean)

    ERROR_KEYWORDS = (
        "error", "failed", "malformed", "denied", "refused", "timeout",
        "cannot", "unable", "fatal", "panic", "warning", "kill process",
        "notready", "not ready", "stopped posting", "unreachable",
        "exception", "traceback", "exit status", "permission",
    )
    TABLE_HEADER_PATTERN = re.compile(r"^[A-Z][A-Z\s/_-]{5,}$")

    # 오류 키워드 포함된 라인 우선 (텍스트 먼저, 그 다음 코드 내용)
    for candidate in text_lines + code_lines:
        low = candidate.lower()
        if any(kw in low for kw in ERROR_KEYWORDS):
            return one_line(candidate, limit=220)

    # 테이블 헤더처럼 보이는 줄 제외하고 첫 코드 줄 선택
    for candidate in code_lines:
        if not TABLE_HEADER_PATTERN.match(candidate.strip()):
            return one_line(candidate, limit=220)

    # 최후 폴백: 첫 텍스트 줄
    if text_lines:
        return one_line(text_lines[0], limit=220)

    return ""


def markdown_list_items(value: str) -> list[str]:
    items: list[str] = []
    for line in value.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            clean = strip_markdown_marker(stripped)
            if clean:
                items.append(clean)
    if items:
        return unique_list(items)
    clean = re.sub(r"```.*?```", "", value, flags=re.S).strip()
    return [one_line(clean)] if clean and "\n" not in clean else []


def resolution_summaries(value: str) -> list[str]:
    summaries: list[str] = []
    for match in re.finditer(r"\*\*(.+?)\*\*", value):
        clean = strip_markdown_marker(match.group(1))
        if clean and len(clean) >= 5:
            summaries.append(clean)
    if summaries:
        return unique_list(summaries)
    return markdown_list_items(value)


def build_problem_type_page(problem: dict[str, Any], record: dict[str, Any]) -> str:
    symptoms = unique_list([*problem.get("symptoms", []), *representative_symptoms(record)])
    tags = unique_list(problem.get("tags", []) + extract_tags(record.get("raw", "")))
    title = representative_page_title(problem, record)
    cause_types = cause_type_block(record)

    return (
        f"# {title}\n\n"
        "## 대표 증상\n\n"
        f"{bullet_list(symptoms)}\n\n"
        "---\n\n"
        "## 원인\n\n"
        f"{problem['cause']}\n\n"
        "---\n\n"
        "## 원인 유형\n\n"
        f"{cause_types}\n\n"
        "---\n\n"
        "## 검색 태그\n\n"
        f"{', '.join(tags)}\n\n"
        "---\n"
    )


def append_unique_bullets(content: str, heading: str, values: list[str]) -> str:
    values = [value for value in unique_list(values) if value]
    if not values:
        return content
    existing_section = extract_section(content, heading)
    existing_items = set(re.findall(r"^- `?(.+?)`?\s*$", existing_section, flags=re.M))
    new_lines = [format_list_item(value) for value in values if value not in existing_items]
    if not new_lines:
        return content
    return append_to_section(content, heading, "\n".join(new_lines))


def append_case_to_problem_page(existing_content: str, record: dict[str, Any]) -> str:
    content = existing_content
    if record["source_path"] not in extract_section(content, "원인 유형"):
        content = append_to_section(content, "원인 유형", f"{cause_type_block(record)}\n\n---")
    symptoms = representative_symptoms(record)
    if symptoms:
        content = append_unique_bullets(content, "대표 증상", symptoms)
    return content


def extract_section(content: str, heading: str) -> str:
    pattern = rf"^## {re.escape(heading)}\s*\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, content, flags=re.M | re.S)
    return match.group("body").strip() if match else ""


def append_to_section(content: str, heading: str, addition: str) -> str:
    addition = addition.strip()
    if not addition:
        return content
    pattern = rf"(^## {re.escape(heading)}\s*\n)(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, content, flags=re.M | re.S)
    if not match:
        return content.rstrip() + f"\n\n## {heading}\n\n{addition}\n"
    body = match.group("body").rstrip()
    divider_match = re.search(r"(?:\n\s*)?---\s*$", body)
    if divider_match:
        body = body[: divider_match.start()].rstrip()
        if addition.endswith("---"):
            replacement_body = body + "\n\n---\n\n" + addition
        else:
            replacement_body = body + "\n\n" + addition + "\n\n---"
    else:
        replacement_body = body + "\n\n" + addition
    replacement = match.group(1) + replacement_body.strip() + "\n\n"
    return content[: match.start()] + replacement + content[match.end():]


def metadata_from_content(entry: dict[str, Any], content: str) -> dict[str, Any]:
    symptoms = bullet_values(extract_section(content, "대표 증상"))
    cases = parse_cases(content)
    source_paths = unique_list([case["source"] for case in cases if case.get("source")])
    tags = extract_search_tags(content) or extract_tags(content)
    entry.update(
        {
            "title": extract_title(content, entry.get("title", "")),
            "tags": tags,
            "symptoms": symptoms,
            "case_count": len(cases),
            "source_paths": source_paths,
            "status": entry.get("status", "draft"),
            "updated_at": today_kst(),
        }
    )
    return entry


def bullet_values(section: str) -> list[str]:
    values = []
    for line in section.splitlines():
        match = re.match(r"^-\s+(.+?)\s*$", line.strip())
        if match:
            value = strip_markdown_marker(match.group(1))
            if value not in {"`", "``", "```"}:
                values.append(value)
    return unique_list(values)


def extract_search_tags(content: str) -> list[str]:
    section = extract_section(content, "검색 태그")
    if not section:
        return []
    return unique_list([part.strip() for part in re.split(r"[,#\s]+", section) if part.strip() and part.strip() != "---"])


def parse_case_lines(section: str) -> list[dict[str, str]]:
    cases: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in section.splitlines():
        if line.startswith("### "):
            if current:
                cases.append(current)
            current = {"title": line[4:].strip()}
        elif line.startswith("- 원본:"):
            src = line.split(":", 1)[1].strip().strip("`")
            if current and "source" in current:
                cases.append(current)
                current = {"source": src}
            elif current:
                current["source"] = src
            else:
                current = {"source": src}
        elif current and line.startswith("- 상황:"):
            current["context"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("- 해결 요약:"):
            current["resolution"] = line.split(":", 1)[1].strip()
        elif current and line.startswith("- 해결:"):
            current["resolution"] = line.split(":", 1)[1].strip()
    if current:
        cases.append(current)
    return cases


def parse_cases(content: str) -> list[dict[str, str]]:
    section = extract_section(content, "발생 사례")
    if section:
        return parse_case_lines(section)

    cause_section = extract_section(content, "원인 유형")
    summary_blocks: list[str] = []
    for match in re.finditer(r"^###\s+(.+?)\s*\n(?P<body>.*?)(?=^###\s+|\Z)", cause_section, flags=re.M | re.S):
        body = match.group("body").strip()
        summary_block = extract_labeled_block(body, "요약") or extract_labeled_block(body, "사례")
        if summary_block:
            summary_blocks.append(summary_block)
    return parse_case_lines("\n\n".join(summary_blocks))


def extract_labeled_block(content: str, label: str) -> str:
    pattern = rf"^{re.escape(label)}:\s*\n(?P<body>.*?)(?=^(?:증상|원인|확인|해결|사례|요약):\s*$|\Z)"
    match = re.search(pattern, content, flags=re.M | re.S)
    return match.group("body").strip() if match else ""


def parse_cause_types(content: str) -> list[dict[str, Any]]:
    section = extract_section(content, "원인 유형")
    cause_types: list[dict[str, Any]] = []
    for match in re.finditer(r"^###\s+(.+?)\s*\n(?P<body>.*?)(?=^###\s+|\Z)", section, flags=re.M | re.S):
        title = match.group(1).strip()
        body = match.group("body").strip()
        symptoms = bullet_values(extract_labeled_block(body, "증상"))
        checks = ordered_values(extract_labeled_block(body, "확인"))
        resolutions = bullet_values(extract_labeled_block(body, "해결"))
        summary_block = extract_labeled_block(body, "요약") or extract_labeled_block(body, "사례")
        cases = parse_case_lines(summary_block)
        cause_types.append(
            {
                "title": title,
                "symptoms": symptoms,
                "checks": checks,
                "resolution_strategy": resolutions,
                "related_cases": cases,
                "content": body,
            }
        )
    return cause_types


def best_cause_type(query: str, content: str) -> dict[str, Any] | None:
    tokens = search_tokens(query)
    best: dict[str, Any] | None = None
    best_score = 0
    for cause_type in parse_cause_types(content):
        score, matched_specific = score_text(tokens, cause_type["title"], [], cause_type["symptoms"], cause_type["content"])
        if matched_specific and score > best_score:
            best = {**cause_type, "score": score, "matched_specific_terms": matched_specific}
            best_score = score
    return best


def normalize_search_token(token: str) -> str:
    token = token.lower().strip("_-")
    aliases = {
        "mounts": "mount",
        "mounted": "mount",
        "mounting": "mount",
        "volumes": "volume",
        "containers": "container",
        "registries": "registry",
        "certs": "certificate",
        "cert": "certificate",
        "timeout": "timedout",
        "timed": "timedout",
        "timeouts": "timedout",
        "eaddrinuse": "addressinuse",
        "allocated": "addressinuse",
    }
    return aliases.get(token, token)


def search_tokens(text: str) -> list[str]:
    tokens = re.split(r"[^a-zA-Z0-9가-힣_]+", text.lower())
    normalized = [normalize_search_token(token) for token in tokens if len(token) >= 2]
    return unique_list(normalized)


def specific_search_tokens(tokens: list[str]) -> list[str]:
    return [token for token in tokens if token not in LOW_SIGNAL_SEARCH_TOKENS and len(token) >= 3]


def search_phrases(tokens: list[str]) -> list[str]:
    phrases: list[str] = []
    for size in range(min(4, len(tokens)), 1, -1):
        for index in range(0, len(tokens) - size + 1):
            group = tokens[index : index + size]
            if any(token not in LOW_SIGNAL_SEARCH_TOKENS for token in group):
                phrases.append(" ".join(group))
    return unique_list(phrases)


def field_match_score(query_tokens: list[str], field_tokens: list[str], weight: int) -> int:
    field_set = set(field_tokens)
    return sum(weight for token in query_tokens if token in field_set)


def phrase_match_score(phrases: list[str], normalized_field: str, weight: int) -> int:
    return sum(weight for phrase in phrases if phrase in normalized_field)


def normalized_search_text(text: str) -> str:
    return " ".join(search_tokens(text))


def score_text(query_tokens: list[str], title: str, tags: list[str], symptoms: list[str], content: str) -> tuple[int, int]:
    specific_tokens = specific_search_tokens(query_tokens)
    phrases = search_phrases(query_tokens)
    title_tokens = search_tokens(title)
    tag_tokens = search_tokens(" ".join(tags))
    symptom_tokens = search_tokens(" ".join(symptoms))
    content_tokens = search_tokens(content)
    content_set = set(content_tokens)

    matched_specific = len(set(specific_tokens) & (set(title_tokens) | set(tag_tokens) | set(symptom_tokens) | content_set))
    if specific_tokens and matched_specific == 0:
        return 0, 0

    title_text = normalized_search_text(title)
    tag_text = normalized_search_text(" ".join(tags))
    symptom_text = normalized_search_text(" ".join(symptoms))
    content_text = normalized_search_text(content)

    score = 0
    score += field_match_score(query_tokens, title_tokens, 16)
    score += field_match_score(query_tokens, symptom_tokens, 14)
    score += field_match_score(query_tokens, tag_tokens, 8)
    score += min(sum(2 for token in query_tokens if token in content_set), 18)
    score += phrase_match_score(phrases, title_text, 40)
    score += phrase_match_score(phrases, symptom_text, 36)
    score += phrase_match_score(phrases, tag_text, 18)
    score += phrase_match_score(phrases, content_text, 10)
    score += matched_specific * 12

    if specific_tokens and matched_specific == len(set(specific_tokens)):
        score += 24
    if query_tokens and " ".join(query_tokens) in content_text:
        score += 45

    return score, matched_specific


def search_wiki(query: str, category: str | None = None, limit: int = 5) -> list[dict[str, Any]]:
    words = search_tokens(query)
    entries = read_index()
    results: list[dict[str, Any]] = []
    for entry in entries:
        if category and entry.get("category") != category:
            continue
        path = ROOT / entry["path"]
        content = read_text(path) if path.exists() else ""
        score, matched_specific = score_text(words, entry.get("title", ""), entry.get("tags", []), entry.get("symptoms", []), content)
        if score > 0:
            snippet = content.replace("\n", " ")[:180]
            results.append({**entry, "score": score, "matched_specific_terms": matched_specific, "snippet": snippet})
    results.sort(key=lambda item: (-item["score"], -item["matched_specific_terms"], item["title"]))
    log_action("Wiki Retrieval Worker", f'called search_wiki("{query}")')
    return results[:limit]


def get_wiki_page(slug: str) -> dict[str, Any]:
    for entry in read_index():
        if entry["slug"] == slug:
            path = ROOT / entry["path"]
            if not path.exists():
                raise FileNotFoundError(entry["path"])
            log_action("Wiki Retrieval Worker", f'called get_wiki_page("{slug}")')
            return {"metadata": entry, "content": read_text(path)}
    raise KeyError(f"Unknown wiki slug: {slug}")


def suggest_fix(error_message: str) -> dict[str, Any]:
    matches = search_wiki(error_message, limit=3)
    if matches:
        best = matches[0]
        content = read_text(ROOT / best["path"])
        score = best.get("score", 0)
        if score >= 90:
            confidence = "high"
        elif score >= 45:
            confidence = "medium"
        else:
            confidence = "low"
        matched_cause_type = best_cause_type(error_message, content)
        recommended_checks = ordered_values(extract_section(content, "확인 순서"))
        resolution_strategy = bullet_values(extract_section(content, "해결 전략"))
        related_cases = parse_cases(content)
        if matched_cause_type:
            recommended_checks = matched_cause_type.get("checks") or recommended_checks
            resolution_strategy = matched_cause_type.get("resolution_strategy") or resolution_strategy
            related_cases = matched_cause_type.get("related_cases") or related_cases
        related_pages = [
            page
            for page in matches
            if page["slug"] == best["slug"] or (page.get("score", 0) >= max(45, score * 0.35) and page.get("matched_specific_terms", 0) >= 2)
        ]
        result = {
            "message": error_message,
            "matched_problem_type": best["title"],
            "matched_cause_type": matched_cause_type["title"] if matched_cause_type else None,
            "confidence": confidence,
            "recommended_checks": recommended_checks,
            "resolution_strategy": resolution_strategy,
            "related_cases": related_cases,
            "related_pages": related_pages,
        }
        log_action("Fix Recommendation Worker", f'called suggest_fix matched={best["slug"]}')
        return result

    log_action("Fix Recommendation Worker", "called suggest_fix fallback")
    return {
        "message": error_message,
        "matched_problem_type": None,
        "confidence": "low",
        "recommended_checks": ["에러 메시지의 핵심 키워드를 분리한다.", "관련 process, port, proxy, network 설정을 확인한다.", "해결 후 raw 사건 기록으로 추가한다."],
        "resolution_strategy": [],
        "related_cases": [],
        "related_pages": [],
    }


def ordered_values(section: str) -> list[str]:
    values = []
    for line in section.splitlines():
        match = re.match(r"^\d+\.\s+(.+)$", line.strip())
        if match:
            values.append(strip_markdown_marker(match.group(1)))
    return values


def create_wiki_page(title: str, category: str, content: str, slug: str | None = None) -> dict[str, Any]:
    slug = slug or slugify(title)
    path = page_path(category, slug)
    if path.exists():
        raise FileExistsError(rel_project_path(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    final_content = content if content.startswith("# ") else f"# {title}\n\n{content}"
    path.write_text(final_content.rstrip() + "\n", encoding="utf-8")
    entries = [entry for entry in read_index() if entry["slug"] != slug]
    entry = {
        "slug": slug,
        "title": title,
        "category": category,
        "path": rel_project_path(path),
        "tags": extract_tags(final_content),
        "symptoms": bullet_values(extract_section(final_content, "대표 증상")),
        "case_count": len(parse_cases(final_content)),
        "source_paths": [case["source"] for case in parse_cases(final_content) if case.get("source")],
        "status": "draft",
        "updated_at": today_kst(),
    }
    entries.append(entry)
    write_index(entries)
    log_action("Wiki Editor Worker", f'called create_wiki_page("{title}")')
    return entry


def update_wiki_page(slug: str, content: str) -> dict[str, Any]:
    entries = read_index()
    for entry in entries:
        if entry["slug"] == slug:
            path = ROOT / entry["path"]
            if not path.exists():
                raise FileNotFoundError(entry["path"])
            final_content = content.rstrip() + "\n"
            path.write_text(final_content, encoding="utf-8")
            metadata_from_content(entry, final_content)
            write_index(entries)
            log_action("Wiki Editor Worker", f'called update_wiki_page("{slug}")')
            return entry
    raise KeyError(f"Unknown wiki slug: {slug}")


def lint_wiki() -> dict[str, Any]:
    entries = read_index()
    by_path = {entry["path"]: entry for entry in entries}
    by_slug: dict[str, dict[str, Any]] = {}
    repaired = 0
    missing_paths: list[str] = []
    duplicate_slugs: list[str] = []
    slug_path_mismatches: list[dict[str, str]] = []
    missing_raw_sources: list[dict[str, str]] = []
    missing_sections: list[dict[str, Any]] = []
    broad_slugs: list[dict[str, str]] = []
    rule_slugs_without_page: list[str] = []
    for category in CATEGORIES:
        category_dir = WIKI_DIR / category
        category_dir.mkdir(parents=True, exist_ok=True)
        for md_path in category_dir.glob("*.md"):
            rel_path = rel_project_path(md_path)
            if rel_path not in by_path:
                content = read_text(md_path)
                title = extract_title(content, md_path.stem.replace("-", " ").title())
                entries.append(metadata_from_content({"slug": md_path.stem, "title": title, "category": category, "path": rel_path}, content))
                repaired += 1
    for entry in entries:
        slug = entry.get("slug", "")
        category = entry.get("category", "")
        expected_path = f"wiki/{category}/{slug}.md"
        if slug in by_slug:
            duplicate_slugs.append(slug)
        by_slug[slug] = entry
        if entry.get("path") != expected_path:
            slug_path_mismatches.append({"slug": slug, "path": entry.get("path", ""), "expected_path": expected_path})
        path = ROOT / entry["path"]
        if not path.exists():
            missing_paths.append(entry["path"])
            continue
        content = read_text(path)
        metadata_from_content(entry, content)
        missing = [heading for heading in REQUIRED_PAGE_SECTIONS if not extract_section(content, heading)]
        if missing:
            missing_sections.append({"slug": slug, "missing_sections": missing})
        for source_path in entry.get("source_paths", []):
            if not (ROOT / source_path).exists():
                missing_raw_sources.append({"slug": slug, "source_path": source_path})
        if slug in {"docker", "ec2", "kubernetes", "github-actions"}:
            broad_slugs.append({"slug": slug, "path": entry.get("path", "")})
    rule_slugs = {rule["slug"] for rule in PROBLEM_RULES}
    index_slugs = {entry.get("slug", "") for entry in entries}
    rule_slugs_without_page = sorted(rule_slugs - index_slugs)
    write_index(entries)
    log_action("Wiki Editor Worker", "called lint_wiki")
    issues = {
        "missing_paths": missing_paths,
        "duplicate_slugs": sorted(duplicate_slugs),
        "slug_path_mismatches": slug_path_mismatches,
        "missing_raw_sources": missing_raw_sources,
        "missing_sections": missing_sections,
        "broad_slugs": broad_slugs,
        "rule_slugs_without_page": rule_slugs_without_page,
    }
    blocking_issue_keys = (
        "missing_paths",
        "duplicate_slugs",
        "slug_path_mismatches",
        "missing_raw_sources",
        "missing_sections",
        "broad_slugs",
    )
    return {
        "ok": not any(issues[key] for key in blocking_issue_keys),
        "repaired": repaired,
        "pages": len(entries),
        "issues": issues,
    }


def list_categories() -> list[str]:
    log_action("Wiki Retrieval Worker", "called list_categories")
    return list(CATEGORIES)


def resolve_raw_path(source_path: str) -> Path:
    path = Path(source_path)
    if not path.is_absolute():
        path = ROOT / source_path
    if not path.exists():
        candidate = RAW_DIR / source_path
        if candidate.exists():
            path = candidate
        else:
            raise FileNotFoundError(source_path)
    resolved = path.resolve()
    if RAW_DIR.resolve() not in resolved.parents:
        raise ValueError("ingest_source only accepts files inside raw/sources/")
    return resolved


def ingest_source(source_path: str) -> dict[str, Any]:
    path = resolve_raw_path(source_path)
    raw = read_text(path)
    record = normalize_raw_record(raw, path)
    problem = infer_problem_type(record)
    log_action("Orchestrator", f"received raw source: {path.name}")
    log_action("Source Ingestion Worker", f"parsed sections for {record['title']}")
    log_action("Error Pattern Worker", f"inferred problem_type={problem['title']}")

    existing = find_related_problem_page(problem)
    if existing:
        content = append_case_to_problem_page(read_text(ROOT / existing["path"]), record)
        entry = update_wiki_page(existing["slug"], content)
        action = "updated"
    else:
        content = build_problem_type_page(problem, record)
        entry = create_wiki_page(problem["title"], problem["category"], content, slug=problem["slug"])
        action = "created"

    return {"action": action, "problem_type": problem["title"], "page": entry, "record": {"title": record["title"], "source_path": record["source_path"]}}


def list_tools() -> list[str]:
    return [
        "search_wiki(query, category=None, limit=5)",
        "get_wiki_page(slug)",
        "suggest_fix(error_message)",
        "create_wiki_page(title, category, content)",
        "update_wiki_page(slug, content)",
        "lint_wiki()",
        "list_categories()",
        "ingest_source(source_path)",
    ]


def print_json(data: Any) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def main() -> None:
    if sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Infra Error Archive wiki server")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list-tools")

    search_parser = sub.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--category", choices=CATEGORIES)
    search_parser.add_argument("--limit", type=int, default=5)

    get_parser = sub.add_parser("get-page")
    get_parser.add_argument("slug")

    suggest_parser = sub.add_parser("suggest-fix")
    suggest_parser.add_argument("error_message")

    create_parser = sub.add_parser("create-page")
    create_parser.add_argument("title")
    create_parser.add_argument("category", choices=CATEGORIES)
    create_parser.add_argument("content")

    update_parser = sub.add_parser("update-page")
    update_parser.add_argument("slug")
    update_parser.add_argument("content")

    sub.add_parser("lint")
    sub.add_parser("list-categories")

    ingest_parser = sub.add_parser("ingest-source")
    ingest_parser.add_argument("source_path")

    args = parser.parse_args()

    if args.command == "list-tools":
        print_json(list_tools())
    elif args.command == "search":
        print_json(search_wiki(args.query, args.category, args.limit))
    elif args.command == "get-page":
        print_json(get_wiki_page(args.slug))
    elif args.command == "suggest-fix":
        print_json(suggest_fix(args.error_message))
    elif args.command == "create-page":
        print_json(create_wiki_page(args.title, args.category, args.content))
    elif args.command == "update-page":
        print_json(update_wiki_page(args.slug, args.content))
    elif args.command == "lint":
        print_json(lint_wiki())
    elif args.command == "list-categories":
        print_json(list_categories())
    elif args.command == "ingest-source":
        print_json(ingest_source(args.source_path))


if __name__ == "__main__":
    main()
