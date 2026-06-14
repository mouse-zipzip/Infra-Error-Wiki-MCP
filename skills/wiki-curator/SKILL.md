# Wiki Curator Skill

이 Skill은 외부 Agent가 `raw/sources/`의 인프라 오류 기록을 이 저장소의 Wiki Page로 통합할 때 사용하는 실행 절차입니다.

## 언제 사용하는가

- 새 raw 오류 기록을 Wiki에 추가할 때
- 기존 Wiki와 비슷한 사건인지 확인할 때
- 오류 메시지에 대한 확인 순서와 해결 요약을 찾을 때
- Wiki 생성 후 검증 결과를 보고할 때

## 반드시 읽을 컨텍스트

작업 전 다음 파일을 읽습니다.

1. `RULES.md`
2. `docs/01-domain-definition.md`
3. `docs/03-prd-spec.md`
4. `schema/raw-source-template.md`
5. `schema/wiki-page-template.md`
6. 대상 raw 파일: `raw/sources/<file>.md`

## 실행 절차

1. 대상 raw 파일이 `raw/sources/` 아래에 있는지 확인합니다.
2. `schema/raw-source-template.md`를 기준으로 raw에서 원본 오류 메시지, 상황, 원인, 해결 내용을 파악합니다.
3. `RULES.md`의 병합 판단 기준으로 기존 Page와의 유사성을 검토합니다. 최종 생성 또는 병합은 `ingest-source` Tool 실행 결과를 기준으로 확인합니다.
4. Tool 목록을 확인합니다.

   ```powershell
   python tools/wiki_mcp_server.py list-tools
   ```

5. raw 기록을 Wiki에 통합합니다.

   ```powershell
   python tools/wiki_mcp_server.py ingest-source raw/sources/<file>.md
   ```

6. Wiki 정합성을 검사합니다.

   ```powershell
   python tools/wiki_mcp_server.py lint
   ```

7. 원본 오류 메시지로 검색 또는 해결 추천을 확인합니다.

   ```powershell
   python tools/wiki_mcp_server.py suggest-fix "<error message>"
   ```

8. 생성 또는 수정된 Wiki Page가 `schema/wiki-page-template.md`의 구조를 따르고 raw 출처를 추적할 수 있는지 확인합니다.
9. Wiki 내용이 raw 원본과 충돌하지 않는지 비교합니다.
10. raw 파일이 수정되거나 삭제되지 않았는지 확인합니다.
11. git을 사용할 수 있으면 변경 범위를 확인합니다.

   ```powershell
   git diff -- wiki/ raw/sources/
   ```

12. 변경된 Wiki Page, index 갱신 여부, 검증 결과를 보고합니다.

## 화면 검증

화면 확인이 필요하면 Viewer를 실행합니다.

```powershell
python tools/viewer_server.py
```

브라우저에서 다음 주소를 엽니다.

```text
http://127.0.0.1:8000/
```

## 실패 처리

Tool 실패, lint 실패, raw-Wiki 불일치가 있으면 작업을 완료한 것처럼 보고하지 않습니다. `RULES.md`의 실패 시 보고 형식에 따라 실패 상태를 보고합니다.
