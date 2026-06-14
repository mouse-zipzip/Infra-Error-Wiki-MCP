# GitHub Actions 잡이 의도하지 않은 러너에서 실행됨

## 발생한 오류

명시적인 에러 없이, 잡이 예상한 러너(self-hosted runner 또는 특정 GitHub-hosted runner)가 아닌 다른 러너에서 실행됨. 환경 차이로 인해 잡이 실패하거나 예상과 다른 결과 발생.

## 당시 상황

- self-hosted runner와 GitHub-hosted runner를 혼용하는 환경
- self-hosted runner에 `ubuntu-latest`, `windows-latest` 등 preset label과 동일한 label을 지정한 경우
- 잡의 `runs-on:` 에 러너 label을 지정했으나 의도한 러너가 선택되지 않음

## 확인한 내용

self-hosted runner의 label 목록 확인:

GitHub 저장소 또는 조직 → Settings → Actions → Runners → 해당 runner 클릭 → Labels 확인

현재 잡의 `runs-on:` 값 확인:

```yaml
jobs:
  build:
    runs-on: ubuntu-latest  # preset label과 동일한 경우 문제 발생
```

GitHub-hosted runner가 사용하는 preset label 목록:
- `ubuntu-latest`, `ubuntu-22.04`, `ubuntu-20.04`
- `windows-latest`, `windows-2022`
- `macos-latest`, `macos-13` 등

## 원인

GitHub Actions는 `runs-on:` label이 매칭되는 러너 중 하나를 선택함. self-hosted runner에 `ubuntu-latest` 같은 preset label을 그대로 붙이면, 해당 잡이 GitHub-hosted runner 또는 self-hosted runner 중 무작위로 선택될 수 있음. 어느 러너에서 실행될지 보장되지 않음.

## 해결 방법

**방법 1: self-hosted runner에 고유한 label 사용**

```yaml
# self-hosted runner에 'self-hosted-prod', 'gpu-runner' 같은 고유 label 지정
jobs:
  build:
    runs-on: self-hosted-prod
```

**방법 2: `self-hosted` label 조합 사용**

```yaml
jobs:
  build:
    runs-on: [self-hosted, linux, x64]
```

`self-hosted` label을 포함하면 GitHub-hosted runner와 구별됨.

**방법 3: preset label과 중복되지 않는 명명 규칙 적용**

self-hosted runner label은 팀 컨벤션에 따라 prefix를 붙여 명명:

```
on-prem-ubuntu-22
gpu-runner-01
build-server-large
```

## 재발 방지

- self-hosted runner 등록 시 preset label과 절대 동일한 이름을 사용하지 않음
- self-hosted runner label 명명 규칙을 팀 문서로 정의하고 신규 runner 등록 시 체크
- `runs-on:` 값을 리뷰할 때 preset label 목록과 대조 확인

## 참고

- https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/troubleshooting-workflows
- https://github.com/actions/runner-images
