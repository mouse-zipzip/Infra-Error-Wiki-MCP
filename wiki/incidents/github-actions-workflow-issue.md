# GitHub Actions Workflow Issue

## 대표 증상

- 워크플로우가 트리거되지 않음
- `취소(Cancel) 후에도 잡이 계속 실행됨`
- 의도하지 않은 러너에서 잡이 실행됨
- `GitHub UI 또는 API로 워크플로우 실행을 취소(Cancel)했으나, 잡(job)이 계속 실행됨. 취소 요청 후에도 실행이 끝나지 않아 무한 대기 상태가 지속됨.`

- `명시적인 에러 없이, 잡이 예상한 러너(self-hosted runner 또는 특정 GitHub-hosted runner)가 아닌 다른 러너에서 실행됨. 환경 차이로 인해 잡이 실패하거나 예상과 다른 결과 발생.`

- `에러 메시지 없이 push 또는 pull request 이후 워크플로우 실행이 생성되지 않음. GitHub Actions 탭에 실행 기록이 나타나지 않거나 "skipped" 상태로 표시됨.`

---

## 원인

워크플로우 비활성화, on: 조건 불일치, always() 함수의 취소 무시, runner label 충돌 등

---

## 원인 유형

### GitHub Actions 워크플로우 취소가 작동하지 않음

증상:
- `GitHub UI 또는 API로 워크플로우 실행을 취소(Cancel)했으나, 잡(job)이 계속 실행됨. 취소 요청 후에도 실행이 끝나지 않아 무한 대기 상태가 지속됨.`

원인:
`always()` 함수는 취소 상태(`cancelled()`)에서도 `true`를 반환하도록 설계되어 있음. cleanup 또는 notification 잡에 `if: always()`를 사용하면, 워크플로우 취소 시에도 해당 잡이 실행되어 정상적인 취소가 불가능해짐.

확인:
1. 워크플로우 파일에서 if: 조건에 always() 함수가 사용되고 있는지 확인
2. always() 함수는 이전 잡이 실패하거나 **취소된 경우에도** true를 반환함. 따라서 워크플로우가 취소 신호를 받아도 해당 잡은 계속 실행됨.

해결:
- 방법 1: `always()` 대신 `!cancelled()` 사용
- `방법 2: 취소가 필요한 경우 API 강제 취소 사용`

요약:
- 원본: `raw/sources/github-actions-always-prevents-cancellation.md`
- 상황: GitHub Actions UI에서 "Cancel workflow" 버튼을 눌렀거나 REST API로 취소 요청을 보냄
- 해결 요약: 방법 1: `always()` 대신 `!cancelled()` 사용

---

### GitHub Actions 잡이 의도하지 않은 러너에서 실행됨

증상:
- `명시적인 에러 없이, 잡이 예상한 러너(self-hosted runner 또는 특정 GitHub-hosted runner)가 아닌 다른 러너에서 실행됨. 환경 차이로 인해 잡이 실패하거나 예상과 다른 결과 발생.`

원인:
GitHub Actions는 `runs-on:` label이 매칭되는 러너 중 하나를 선택함. self-hosted runner에 `ubuntu-latest` 같은 preset label을 그대로 붙이면, 해당 잡이 GitHub-hosted runner 또는 self-hosted runner 중 무작위로 선택될 수 있음. 어느 러너에서 실행될지 보장되지 않음.

확인:
1. 현재 잡의 runs-on: 값 확인
2. ubuntu-latest, ubuntu-22.04, ubuntu-20.04
3. windows-latest, windows-2022
4. macos-latest, macos-13 등

해결:
- `방법 1: self-hosted runner에 고유한 label 사용`
- 방법 2: `self-hosted` label 조합 사용
- `방법 3: preset label과 중복되지 않는 명명 규칙 적용`

요약:
- 원본: `raw/sources/github-actions-runner-label-conflict.md`
- 상황: self-hosted runner와 GitHub-hosted runner를 혼용하는 환경
- 해결 요약: 방법 1: self-hosted runner에 고유한 label 사용

---

### GitHub Actions 워크플로우가 실행되지 않음

증상:
- `에러 메시지 없이 push 또는 pull request 이후 워크플로우 실행이 생성되지 않음. GitHub Actions 탭에 실행 기록이 나타나지 않거나 "skipped" 상태로 표시됨.`

원인:
- 워크플로우가 수동으로 비활성화된 상태
- `on:` 조건이 현재 이벤트(브랜치, 태그, 경로)와 맞지 않음
- `issues`, `schedule` 이벤트가 기본 브랜치 외의 브랜치에서 정의됨
- `커밋 메시지에 skip 어노테이션이 포함됨`
- PR에 머지 충돌이 있음
- `스케줄 워크플로우가 GitHub Actions 서버 부하 시간(매 시간 정각)에 집중되어 지연/드롭됨`

확인:
1. 2. on: 트리거 조건 검토
2. .github/workflows/ 의 YAML 파일에서 on: 섹션 확인
3. issues, schedule 등 일부 이벤트는 **기본 브랜치(default branch)** 에 워크플로우 파일이 있어야만 동작함. 다른 브랜치에서는 트리거되지 않음.
4. 커밋 메시지에 [skip ci], [ci skip], skip-checks:true 등이 포함되어 있으면 워크플로우가 실행되지 않음.
5. paths: 필터가 설정된 경우 변경된 파일이 300개를 초과하면 필터가 제대로 동작하지 않아 실행이 스킵될 수 있음.

해결:
- `cron: '5 * * * *'`

요약:
- 원본: `raw/sources/github-actions-workflow-not-triggered.md`
- 상황: 코드를 push했는데 워크플로우가 실행되지 않을 때
- 해결 요약: cron: '5 * * * *'

---

## 검색 태그

github, github-actions, workflow, runner, ci-cd

---
