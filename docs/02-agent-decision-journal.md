# Agent 작업 Journal

이 문서는 Infra Error Archive를 설계하면서 정한 주요 결정과 이유를 기록합니다. 실제 Tool 실행 기록은 `logs/agent-actions.log`에 남고, 이 문서는 설계 방향과 구현 판단을 설명하는 보조 자료입니다.

## Iteration 1: 도메인 결정

| 항목 | 내용 |
| --- | --- |
| 결정 | 프로젝트 도메인을 인프라 오류 기록 기반 LLM Wiki로 정했습니다. |
| 이유 | 과제 요구사항의 Wiki, Agent, Tool, Viewer를 하나의 실행 가능한 제품으로 묶기에 적합하고, 실제 오류 기록을 raw evidence로 보존할 수 있기 때문입니다. |
| 결과 | `raw/sources/`의 오류 기록을 문제 유형별 Wiki로 통합하는 방향을 채택했습니다. |

## Iteration 2: Raw 우선 원칙

| 항목 | 내용 |
| --- | --- |
| 결정 | raw source를 가장 높은 우선순위의 근거로 둡니다. |
| 이유 | Agent가 요약하거나 병합하는 과정에서 정보가 축약될 수 있으므로, 원본 기록을 보존해야 검증이 가능합니다. |
| 결과 | `RULES.md`와 `skills/wiki-curator/SKILL.md`에 raw 우선 원칙을 명시했습니다. |

## Iteration 3: Wiki Page 단위

| 항목 | 내용 |
| --- | --- |
| 결정 | raw 파일 1개당 Wiki Page 1개가 아니라, 문제 유형별 Wiki Page를 만듭니다. |
| 이유 | 같은 오류가 여러 상황에서 반복될 수 있으므로, 사건 단위보다 문제 유형 단위가 재사용에 유리합니다. |
| 결과 | `wiki/incidents/`에 문제 유형별 Page를 두고, 같은 유형은 발생 기록으로 누적합니다. |

## Iteration 4: MCP-style Tool 분리

| 항목 | 내용 |
| --- | --- |
| 결정 | Wiki 기능을 MCP-style Tool로 분리했습니다. |
| 이유 | Agent가 파일을 임의로 수정하는 것보다, 정해진 Tool을 통해 검색, 생성, 병합, 검증을 수행하는 편이 추적 가능하고 안정적입니다. |
| 결과 | `tools/wiki_mcp_server.py`를 agent-facing wrapper로 두고, 실제 구현은 `server/wiki_mcp_server.py`에 두었습니다. |

## Iteration 5: Viewer 구조

| 항목 | 내용 |
| --- | --- |
| 결정 | Viewer는 3영역 UI로 구성했습니다. |
| 이유 | 문제 유형 목록, Wiki 상세 내용, 현재 오류 분석 결과를 동시에 확인해야 사용자가 troubleshooting 흐름을 이해하기 쉽습니다. |
| 결과 | `web/`에 UI를 두고, `tools/viewer_server.py`로 실행하도록 정리했습니다. |

## Iteration 6: Agent 하네스 구성

| 항목 | 내용 |
| --- | --- |
| 결정 | `RULES.md`를 Agent 운영지침 파일로, `skills/wiki-curator/SKILL.md`를 Skill로 사용합니다. |
| 이유 | 과제 요구사항의 하네스 항목을 만족하면서, 외부 Agent가 어떤 규칙과 절차로 작업해야 하는지 명확히 설명할 수 있습니다. |
| 결과 | Agent는 RULES와 Skill을 읽고 `list-tools`, `ingest-source`, `lint`, `suggest-fix` 순서로 raw 통합을 수행합니다. |

## Iteration 7: Subagent 모델

| 항목 | 내용 |
| --- | --- |
| 결정 | MVP에서는 Subagent를 별도 프로세스로 실행하지 않고, 하나의 외부 Agent가 역할을 순서대로 수행합니다. |
| 이유 | 실제 실행 복잡도를 줄이면서도 Source Ingestion, Error Pattern, Wiki Retrieval, Case Merge, Fix Recommendation의 책임 경계를 설명할 수 있습니다. |
| 결과 | `RULES.md`에 각 Subagent 역할의 허용 범위와 제한 범위를 표로 정리했습니다. |

## Iteration 8: Viewer의 오류 분석 방식

| 항목 | 내용 |
| --- | --- |
| 결정 | Viewer는 `/api/suggest-fix` 요청을 받으면 로컬 subprocess로 `suggest-fix` Tool을 호출합니다. |
| 이유 | API key나 외부 LLM 없이도 로컬 Wiki 기반 분석 결과를 화면에서 확인할 수 있어야 하기 때문입니다. |
| 결과 | `server/viewer_server.py`가 내부 구현인 `server/wiki_mcp_server.py suggest-fix`를 subprocess로 호출하고, Viewer는 그 결과를 표시합니다. 외부 Agent용 진입점은 `tools/wiki_mcp_server.py`로 유지합니다. |

## Iteration 9: raw 작성 형식

| 항목 | 내용 |
| --- | --- |
| 결정 | raw Markdown은 `## 발생한 오류`, `## 당시 상황`, `## 확인한 내용`, `## 원인`, `## 해결 방법` 같은 제목을 권장합니다. |
| 이유 | 현재 ingest는 제목 기반으로 섹션을 분류하므로, 제목이 일정해야 원인과 해결 요약이 안정적으로 추출됩니다. |
| 결과 | README에 raw 작성 템플릿을 넣고, 원인과 해결이 비어 보이지 않도록 권장 제목을 명시했습니다. |
