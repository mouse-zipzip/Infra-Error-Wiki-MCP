# 도메인 정의

## 프로젝트 도메인

Infra Error Archive는 인프라 오류 기록을 문제 유형별 troubleshooting Wiki로 축적하는 로컬 지식베이스입니다.

목표는 raw 기록을 보기 좋은 문서로 단순 변환하는 것이 아닙니다. 여러 오류 기록에서 반복되는 문제 유형을 찾아, 이후 비슷한 오류가 발생했을 때 확인 순서와 해결 요약을 빠르게 찾을 수 있게 만드는 것입니다.

## 핵심 문제

인프라 오류는 같은 원인이라도 서로 다른 메시지와 상황으로 나타납니다.

예:

- Docker 실행 실패와 Spring Boot 실행 실패가 모두 port binding 문제일 수 있습니다.
- SSH 접속 실패가 key 권한, 네트워크, host key 문제로 나뉠 수 있습니다.
- Docker private registry 오류가 HTTP/HTTPS mismatch 또는 TLS 인증서 신뢰 문제일 수 있습니다.

이 프로젝트는 이런 기록을 raw evidence로 보존하고, Agent와 MCP-style Tool을 통해 재사용 가능한 Wiki Page로 정리합니다.

## 주요 사용자

- 인프라 오류와 배포 문제를 반복해서 기록하고 싶은 개발자
- Docker, EC2, Kubernetes, GitHub Actions 오류를 빠르게 분류하고 싶은 사용자
- raw 기록을 기반으로 Wiki를 관리하는 외부 Agent

## 주요 객체

### Raw Source

`raw/sources/`에 저장되는 원본 자료입니다.

포함할 수 있는 내용:

- 터미널 출력
- 서버 로그
- 오류 메시지
- 당시 상황
- 확인한 내용
- 원인
- 해결 방법
- 참고 링크

raw source는 가장 높은 우선순위의 근거입니다. Wiki 내용과 raw가 충돌하면 raw를 기준으로 판단합니다.

### Problem Type Wiki

`wiki/incidents/`에 저장되는 문제 유형별 Wiki Page입니다.

하나의 Wiki Page는 여러 raw 사건을 일반화해서 다음 내용을 담습니다.

- 대표 증상
- 발생 상황
- 원인 유형
- 확인 순서
- 해결 요약
- 발생 기록
- 출처 raw 파일

예:

- `Port Binding Conflict`
- `EC2 SSH Connection Failure`
- `Docker Private Registry TLS Configuration Failure`

### Wiki Index

`wiki/index.json`은 Viewer와 검색 도구가 사용하는 metadata입니다.

주요 필드:

- `slug`
- `title`
- `category`
- `path`
- `tags`
- `symptoms`
- `case_count`
- `source_paths`
- `updated_at`

### MCP-style Tool

Agent가 Wiki를 관리하기 위해 호출하는 CLI 도구입니다.

주요 진입점:

```powershell
python tools/wiki_mcp_server.py list-tools
```

실제 구현은 `server/wiki_mcp_server.py`에 있고, `tools/wiki_mcp_server.py`는 agent-facing wrapper입니다.

### Viewer

브라우저에서 Wiki를 확인하는 UI입니다.

실행:

```powershell
python tools/viewer_server.py
```

접속:

```text
http://127.0.0.1:8000/
```

Viewer는 세 영역으로 구성됩니다.

- 왼쪽: 문제 유형 목록과 검색
- 가운데: 선택한 Wiki Page
- 오른쪽: 현재 오류 메시지 입력과 분석 결과

## Raw에서 Wiki로 가는 흐름

```text
raw/sources/에 오류 기록 추가
        ↓
ingest-source 실행
        ↓
오류 메시지, 상황, 원인, 해결 내용 추출
        ↓
문제 유형 후보 판단
        ↓
기존 Wiki 검색
        ↓
같은 유형이면 기존 Page에 발생 기록 추가
다른 유형이면 새 Wiki Page 생성
        ↓
wiki/index.json 갱신
        ↓
lint와 suggest-fix로 검증
```

## 범위

포함하는 것:

- raw 오류 기록 저장
- 문제 유형별 Wiki Page 생성과 병합
- `wiki/index.json` metadata 관리
- 현재 오류 메시지 기반 검색과 해결 힌트 제공
- 브라우저 Viewer
- Agent 운영지침과 Skill 기반 하네스

제외하는 것:

- 외부 LLM API 필수 연동
- API key 하드코딩
- raw 원본 자동 삭제
- Wiki에 없는 내용을 확정 답변처럼 생성
- 운영 모니터링 시스템과의 실시간 연동

## MVP가 답해야 하는 질문

- 이 오류는 어떤 문제 유형에 가까운가?
- 과거에도 같은 유형의 문제가 있었는가?
- 먼저 무엇을 확인해야 하는가?
- raw 기록에 근거한 해결 요약은 무엇인가?
- 현재 Wiki에 관련 지식이 없을 때 어떻게 안내하는가?
