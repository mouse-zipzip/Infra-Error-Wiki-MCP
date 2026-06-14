# PRD / SPEC

## Goal

Infra Error Archive는 사용자가 겪은 인프라 오류 기록과 공개 troubleshooting 자료를 `raw/sources/`에 저장하고, 이를 문제 유형별 Wiki로 통합하는 로컬 LLM Wiki 도구입니다.

처음 보는 사용자가 repo를 clone한 뒤 raw 자료 1건을 넣고, 명령어 몇 개로 Wiki Page를 만들고, Viewer에서 결과를 확인할 수 있어야 합니다.

## Problem

인프라 오류 기록은 터미널 출력, 서버 로그, 배포 메모, 개인 메모처럼 흩어져 있습니다. 구조화된 지식베이스가 없으면 같은 오류를 반복해서 검색하게 됩니다.

이 프로젝트는 다음 문제를 해결합니다.

- 실제 오류 기록을 raw evidence로 보존합니다.
- 반복되는 오류를 문제 유형별 Wiki Page로 정리합니다.
- 현재 오류 메시지를 기존 Wiki와 비교해 관련 문제 유형을 찾습니다.
- raw에 근거한 확인 순서와 해결 요약을 제공합니다.
- Viewer에서 Wiki와 오류 분석 결과를 확인합니다.

## Scope

포함:

- `raw/sources/` Markdown 자료 ingest
- 문제 유형 추출과 Wiki Page 생성/병합
- `wiki/index.json` metadata 관리
- 현재 오류 메시지 기반 `suggest-fix`
- 브라우저 Viewer
- `RULES.md`와 `skills/wiki-curator/SKILL.md` 기반 Agent 하네스

제외:

- 외부 LLM API 필수 연동
- API key 하드코딩
- raw 원본 자동 삭제
- Wiki에 없는 해결책을 확정 답변처럼 생성
- 운영 모니터링 시스템 실시간 연동

## Core Requirements

| ID | 요구사항 |
| --- | --- |
| R1 | 사용자는 오류 기록을 `raw/sources/`에 Markdown으로 저장할 수 있어야 합니다. |
| R2 | ingest는 raw에서 오류 메시지, 상황, 확인 내용, 원인, 해결 방법을 가능한 범위에서 추출해야 합니다. |
| R3 | 같은 문제 유형이 이미 있으면 새 Page를 만들지 않고 기존 Wiki Page에 발생 기록을 추가해야 합니다. |
| R4 | 새 문제 유형이면 `wiki/incidents/<slug>.md`를 만들고 `wiki/index.json`을 갱신해야 합니다. |
| R5 | `suggest-fix`는 현재 오류 메시지와 가까운 Wiki Page, 확인 순서, 해결 요약, 과거 발생 기록을 반환해야 합니다. |
| R6 | 관련 Wiki가 없으면 근거 없는 답을 만들지 않고 관련 문제 유형을 찾지 못했다고 안내해야 합니다. |
| R7 | Viewer는 문제 유형 목록, Wiki Page 상세, 현재 오류 분석 결과를 한 화면에서 보여야 합니다. |
| R8 | 모든 Wiki 생성/수정/추천 흐름은 MCP-style Tool로 실행 가능해야 합니다. |
| R9 | Wiki 내용은 raw 원본과 대조 가능해야 하며, 판단 기준은 raw 원본을 우선해야 합니다. |
| R10 | `lint`는 `wiki/index.json`과 실제 Wiki 파일의 정합성을 검사해야 합니다. |

## Raw 작성 권장 형식

현재 ingest는 `##` 제목을 기준으로 섹션을 분류합니다.

권장 제목:

- `## 발생한 오류`
- `## 당시 상황`
- `## 확인한 내용`
- `## 원인`
- `## 해결 방법`
- `## 재발 방지`
- `## 참고`

`## 원인`, `## 해결 방법` 제목을 사용하면 Wiki의 원인/해결 요약이 가장 안정적으로 생성됩니다.

## Raw to Wiki Flow

```text
raw/sources/에 오류 기록 추가
        ↓
python tools/wiki_mcp_server.py ingest-source raw/sources/<file>.md
        ↓
오류 메시지와 주요 섹션 추출
        ↓
문제 유형 후보 판단
        ↓
기존 Wiki 검색
        ↓
기존 유형이면 발생 기록 병합
새 유형이면 Wiki Page 생성
        ↓
wiki/index.json 갱신
        ↓
python tools/wiki_mcp_server.py lint
```

## MCP-style Tools

Tool 목록 확인:

```powershell
python tools/wiki_mcp_server.py list-tools
```

| Tool | CLI | 역할 |
| --- | --- | --- |
| `ingest_source(source_path)` | `ingest-source` | raw 기록을 문제 유형 Wiki로 생성하거나 기존 Wiki에 병합 |
| `search_wiki(query, category=None, limit=5)` | `search` | title, tag, symptoms, content 기반 Wiki 검색 |
| `get_wiki_page(slug)` | `get-page` | 특정 Wiki Page 조회 |
| `suggest_fix(error_message)` | `suggest-fix` | 현재 오류와 가까운 Wiki를 찾아 확인 순서와 해결 요약 반환 |
| `create_wiki_page(title, category, content)` | `create-page` | 새 Wiki Page 생성 |
| `update_wiki_page(slug, content)` | `update-page` | 기존 Wiki Page 수정 |
| `lint_wiki()` | `lint` | Wiki 파일과 index metadata 정합성 검사 |
| `list_categories()` | `list-categories` | Wiki category 목록 반환 |

`tools/wiki_mcp_server.py`는 Agent가 호출하는 진입점이고, 실제 구현은 `server/wiki_mcp_server.py`에 있습니다.

## Agent SPEC

Agent는 저장소를 자유롭게 고치는 일반 챗봇이 아니라 Wiki Curator Agent로 동작합니다.

작업 순서:

```text
1. RULES.md와 skills/wiki-curator/SKILL.md를 읽는다.
2. 대상 raw 파일을 확인한다.
3. list-tools로 Tool 목록을 확인한다.
4. ingest-source로 raw를 Wiki에 통합한다.
5. lint로 Wiki 정합성을 검사한다.
6. 원본 오류 메시지로 search 또는 suggest-fix를 실행한다.
7. Wiki 요약이 raw와 일치하는지 대조한다.
8. 변경 파일과 검증 결과를 보고한다.
```

Subagent 역할은 현재 별도 프로세스가 아니라 하나의 외부 Agent가 순서대로 수행하는 역할 모델입니다.

- Source Ingestion Subagent
- Error Pattern Subagent
- Wiki Retrieval Subagent
- Case Merge Subagent
- Fix Recommendation Subagent

각 역할의 허용 범위와 제한 범위는 `RULES.md`에 정의합니다.

## Viewer SPEC

Viewer 실행:

```powershell
python tools/viewer_server.py
```

접속:

```text
http://127.0.0.1:8000/
```

다른 포트를 사용할 때:

```powershell
python tools/viewer_server.py --port 8080
```

화면 구성:

| 영역 | 내용 |
| --- | --- |
| 왼쪽 | 문제 유형 목록과 검색 |
| 가운데 | 선택한 Wiki Page 상세 |
| 오른쪽 | 현재 오류 메시지 입력과 분석 결과 |

Viewer의 분석 기능은 외부 LLM API를 호출하지 않습니다. `/api/suggest-fix` 요청을 받으면 `server/viewer_server.py`가 subprocess로 내부 구현인 `server/wiki_mcp_server.py suggest-fix`를 실행하고, 기존 Wiki에서 관련 결과를 찾아 표시합니다. 외부 Agent가 직접 호출할 때는 wrapper인 `tools/wiki_mcp_server.py`를 사용합니다.

## Data SPEC

`wiki/index.json`은 Viewer와 검색 도구가 사용하는 metadata입니다.

예:

```json
{
  "slug": "port-binding-conflict",
  "title": "Port Binding Conflict",
  "category": "incidents",
  "path": "wiki/incidents/port-binding-conflict.md",
  "tags": ["port", "bind", "docker"],
  "symptoms": ["address already in use"],
  "case_count": 1,
  "source_paths": ["raw/sources/my-error.md"],
  "status": "draft",
  "updated_at": "2026-06-14"
}
```

## Acceptance Criteria

- `python tools/wiki_mcp_server.py list-tools`가 Tool 목록을 출력합니다.
- `ingest-source`가 raw 기록을 Wiki에 생성하거나 기존 Wiki에 병합합니다.
- `lint`가 `wiki/index.json`과 Wiki 파일 정합성을 검사합니다.
- `search`가 관련 Wiki Page를 반환합니다.
- `suggest-fix`가 관련 Wiki, 확인 순서, 해결 요약, 발생 기록을 반환합니다.
- 관련 Wiki가 없으면 새 답을 지어내지 않고 찾지 못했다고 안내합니다.
- Viewer가 `http://127.0.0.1:8000/`에서 열립니다.
- Viewer가 문제 유형 목록, Wiki Page 상세, 오류 분석 패널을 보여줍니다.
- Wiki 내용은 `source_paths`를 통해 raw 원본으로 추적 가능합니다.
