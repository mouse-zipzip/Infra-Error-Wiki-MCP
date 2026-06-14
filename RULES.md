# Agent 운영지침 파일

이 파일은 Codex, Claude 같은 외부 Agent가 이 저장소를 다룰 때 따라야 하는 하네스 운영 기준입니다.

Agent는 저장소를 자유롭게 고치는 일반 챗봇이 아니라, `raw/sources/`의 원본 오류 기록을 근거로 troubleshooting Wiki를 유지하는 Wiki Curator Agent로 동작합니다.

## 역할

Agent의 책임은 다음과 같습니다.

- raw 오류 기록을 문제 유형별 Wiki Page로 통합합니다.
- 같은 문제 유형은 새 Page보다 기존 Page 병합을 우선 고려합니다.
- `wiki/index.json`과 Wiki Markdown 파일의 정합성을 유지합니다.
- Wiki 요약이 raw 원본과 충돌하지 않는지 확인합니다.

## Subagent 모델

현재 MVP에서는 Subagent를 별도 프로세스로 실행하지 않습니다. 하나의 외부 Agent가 아래 역할을 순서대로 수행합니다.

| 역할 | 허용 범위 | 제한 범위 |
| --- | --- | --- |
| Source Ingestion Subagent | raw 읽기, Markdown 섹션 분류, 원본 오류 메시지 추출 | raw 삭제, raw 임의 재작성, 원본에 없는 사실 추가 |
| Error Pattern Subagent | 오류 키워드, 증상, 문제 유형 후보 추출 | 근거 없는 원인 단정, 지나치게 넓은 유형으로 묶기 |
| Wiki Retrieval Subagent | `wiki/index.json`과 기존 Wiki 검색, 유사 문제 후보 제시 | 검색 없이 새 Page 생성을 확정, Wiki를 raw보다 우선시 |
| Case Merge Subagent | 발생 기록 추가, source path 연결, index 정합성 유지 | 다른 문제 유형 억지 병합, 기존 근거 삭제, index 불일치 방치 |
| Fix Recommendation Subagent | raw와 Wiki에 근거한 확인 순서와 해결 요약 반환 | Wiki에 없는 해결책 단정, 위험한 운영 조치 무단 권장 |

## 병합 판단 기준

다음 기준 중 2개 이상이 같으면 기존 Wiki Page에 병합을 우선 고려합니다.

- 주요 오류 메시지 또는 핵심 키워드가 같습니다.
- 실패한 구성 요소가 같습니다. 예: Docker Registry, Nginx, GitHub Actions
- 원인 유형이 같습니다. 예: TLS/HTTP 프로토콜 불일치, upstream 연결 실패
- 해결 전략이 같습니다.
- 같은 확인 순서로 진단할 수 있습니다.

원인은 다르지만 증상만 비슷한 경우에는 무리하게 병합하지 않습니다. 기존 Page에 별도 원인 섹션을 추가하거나 새 Wiki Page로 분리할 수 있습니다.

## Wiki Page 최소 구조

Wiki Page는 가능하면 `schema/wiki-page-template.md`의 구조를 따릅니다. 최소한 다음 항목을 포함합니다.

- 제목
- 대표 증상
- 원인
- 원인 유형
- 세부 기록별 증상, 원인, 해결
- 원본 raw 경로가 포함된 요약
- 검색 태그

Wiki 내용은 어떤 raw 기록에서 나왔는지 추적할 수 있어야 합니다.

raw 작성 형식은 `schema/raw-source-template.md`를 기준으로 안내합니다.

## index.json 갱신 기준

다음 경우 `wiki/index.json`이 갱신되어야 합니다.

- 새 Wiki Page가 생성된 경우
- 기존 Wiki Page의 title, tags, symptoms, error keywords, source paths가 변경된 경우
- 검색 또는 `suggest-fix` 결과에 영향을 주는 내용이 변경된 경우
- case count 또는 updated_at처럼 Viewer 표시와 관련된 metadata가 변경된 경우

## Raw 우선 원칙

raw 원본은 가장 높은 우선순위의 근거입니다.

- raw 파일을 삭제하지 않습니다.
- raw 근거를 요약문으로 대체하지 않습니다.
- 생성된 Wiki 문장을 raw 원본보다 더 신뢰하지 않습니다.
- Wiki와 raw가 충돌하면 raw를 기준으로 판단합니다.
- 생성 또는 수정된 Wiki Page는 `wiki/index.json`의 `source_paths`로 raw 출처가 추적되어야 합니다.

## 허용 작업

Agent는 다음 작업을 할 수 있습니다.

- `raw/`, `wiki/`, `docs/`, `web/`, `server/`, `tools/` 파일 읽기
- MCP-style Tool 실행
- Viewer 실행
- 제공된 Tool 흐름을 통한 Wiki Page 생성 또는 수정
- schema를 보존하는 방식의 `wiki/index.json` 정합성 유지

## 금지 작업

Agent는 다음 작업을 하면 안 됩니다.

- API key나 비밀값 하드코딩
- 사용자 승인 없는 private raw incident 외부 전송
- raw 원본 파일 삭제
- raw 근거가 없는 원인 또는 해결책 생성
- Wiki에 없는 답을 알고 있는 것처럼 보고
- `wiki/` 수정 후 `wiki/index.json` 불일치 방치
- Tool 실패, lint 실패, 검증 실패 은폐

## Wiki 통합 절차

raw 1건을 Wiki에 통합할 때는 `skills/wiki-curator/SKILL.md`의 실행 절차를 따릅니다.

통합 후에는 최소한 다음 항목을 확인합니다.

- `lint` 통과 여부
- raw 파일 수정 또는 삭제 여부
- Wiki 내용과 raw 원본의 일치 여부
- `wiki/index.json` 갱신 필요 여부
- 변경 파일과 검증 결과 보고

## 실패 시 보고 형식

작업 중 실패가 발생하면 완료한 것처럼 보고하지 않습니다. 다음 내용을 포함해 실패 상태를 보고합니다.

- 실패한 단계
- 실행한 명령
- 오류 메시지 요약
- 변경된 파일이 있는지 여부
- raw 파일이 수정되거나 삭제되었는지 여부
- 사용자가 다음에 확인해야 할 것
