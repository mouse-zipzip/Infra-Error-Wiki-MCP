# GitHub Actions 워크플로우가 실행되지 않음

## 발생한 오류

에러 메시지 없이 push 또는 pull request 이후 워크플로우 실행이 생성되지 않음. GitHub Actions 탭에 실행 기록이 나타나지 않거나 "skipped" 상태로 표시됨.

## 당시 상황

- 코드를 push했는데 워크플로우가 실행되지 않을 때
- pull request를 열었는데 CI 체크가 시작되지 않을 때
- 스케줄(cron)로 설정한 워크플로우가 예상 시간에 실행되지 않을 때

## 확인한 내용

**1. 워크플로우 비활성화 여부 확인**

GitHub 저장소 → Actions 탭 → 해당 워크플로우 선택 → 오른쪽 상단 "..." → Enable workflow 상태 확인.

**2. `on:` 트리거 조건 검토**

`.github/workflows/` 의 YAML 파일에서 `on:` 섹션 확인:

```yaml
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
```

**3. 브랜치 조건 확인**

`issues`, `schedule` 등 일부 이벤트는 **기본 브랜치(default branch)** 에 워크플로우 파일이 있어야만 동작함. 다른 브랜치에서는 트리거되지 않음.

**4. 커밋 메시지 skip 어노테이션 확인**

```
git log --oneline -5
```

커밋 메시지에 `[skip ci]`, `[ci skip]`, `skip-checks:true` 등이 포함되어 있으면 워크플로우가 실행되지 않음.

**5. path 필터 확인**

`paths:` 필터가 설정된 경우 변경된 파일이 300개를 초과하면 필터가 제대로 동작하지 않아 실행이 스킵될 수 있음.

**6. pull request 충돌 여부**

`pull_request` 이벤트는 PR에 머지 충돌(merge conflict)이 있으면 워크플로우가 실행되지 않음.

## 원인

워크플로우가 실행되지 않는 주요 원인:

- 워크플로우가 수동으로 비활성화된 상태
- `on:` 조건이 현재 이벤트(브랜치, 태그, 경로)와 맞지 않음
- `issues`, `schedule` 이벤트가 기본 브랜치 외의 브랜치에서 정의됨
- 커밋 메시지에 skip 어노테이션이 포함됨
- PR에 머지 충돌이 있음
- 스케줄 워크플로우가 GitHub Actions 서버 부하 시간(매 시간 정각)에 집중되어 지연/드롭됨

## 해결 방법

1. Actions 탭에서 워크플로우가 비활성화되어 있다면 재활성화
2. `on:` 섹션에서 트리거 이벤트와 브랜치 조건이 현재 상황과 맞는지 수정
3. `schedule` 이벤트는 기본 브랜치에만 적용되므로, 기본 브랜치의 워크플로우 파일에 정의
4. 커밋 메시지에서 skip 어노테이션 제거 후 재push
5. PR의 머지 충돌 해결 후 재시도
6. 스케줄 워크플로우는 매 시간 정각을 피하도록 cron 표현식 조정:

```yaml
# 정각(0분) 대신 5분으로 설정
schedule:
  - cron: '5 * * * *'
```

## 재발 방지

- 워크플로우 파일을 처음 작성할 때 `workflow_dispatch` 이벤트를 추가하여 수동 실행으로 테스트 가능하게 함
- `on:` 조건 변경 후 실제 이벤트로 트리거되는지 반드시 확인
- 스케줄 워크플로우는 cron 표현식을 명시적으로 문서화하고 정각을 피하도록 설정

## 참고

- https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/troubleshooting-workflows
- https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/events-that-trigger-workflows
