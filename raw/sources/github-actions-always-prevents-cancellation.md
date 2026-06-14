# GitHub Actions 워크플로우 취소가 작동하지 않음

## 발생한 오류

GitHub UI 또는 API로 워크플로우 실행을 취소(Cancel)했으나, 잡(job)이 계속 실행됨. 취소 요청 후에도 실행이 끝나지 않아 무한 대기 상태가 지속됨.

## 당시 상황

- GitHub Actions UI에서 "Cancel workflow" 버튼을 눌렀거나 REST API로 취소 요청을 보냄
- 일부 잡이 `always()` 상태 체크 함수를 사용하는 조건(`if:`)을 포함하고 있음
- 취소 후에도 해당 잡이 여전히 실행 중 상태로 남아 있음

## 확인한 내용

워크플로우 파일에서 `if:` 조건에 `always()` 함수가 사용되고 있는지 확인:

```yaml
jobs:
  cleanup:
    if: always()
    steps:
      - name: Cleanup
        run: echo "cleaning up"
```

`always()` 함수는 이전 잡이 실패하거나 **취소된 경우에도** `true`를 반환함. 따라서 워크플로우가 취소 신호를 받아도 해당 잡은 계속 실행됨.

API로 강제 취소 시도:

```
POST /repos/{owner}/{repo}/actions/runs/{run_id}/force-cancel
```

## 원인

`always()` 함수는 취소 상태(`cancelled()`)에서도 `true`를 반환하도록 설계되어 있음. cleanup 또는 notification 잡에 `if: always()`를 사용하면, 워크플로우 취소 시에도 해당 잡이 실행되어 정상적인 취소가 불가능해짐.

## 해결 방법

**방법 1: `always()` 대신 `!cancelled()` 사용**

취소 시에는 잡을 건너뛰고 싶다면 `cancelled()` 의 역(inverse)을 사용:

```yaml
jobs:
  cleanup:
    if: ${{ !cancelled() }}
    steps:
      - name: Cleanup
        run: echo "cleaning up"
```

이렇게 하면 이전 잡 실패 시에는 실행되지만, 취소 시에는 실행되지 않음.

**방법 2: 취소가 필요한 경우 API 강제 취소 사용**

```bash
curl -X POST \
  -H "Authorization: token <TOKEN>" \
  https://api.github.com/repos/<owner>/<repo>/actions/runs/<run_id>/force-cancel
```

## 재발 방지

- cleanup/notification 잡에 `always()`를 사용할 때 취소 시 동작을 미리 설계에 반영
- 정말 모든 상황(실패 + 취소 포함)에서 실행해야 하는 잡에만 `always()` 사용
- 워크플로우 YAML 작성 시 `if:` 조건에 대한 평가 결과를 job 로그의 system.txt에서 확인 가능함을 팀에 공유

## 참고

- https://docs.github.com/en/actions/monitoring-and-troubleshooting-workflows/troubleshooting-workflows
- https://docs.github.com/en/actions/writing-workflows/choosing-when-your-workflow-runs/using-conditions-to-control-job-execution
