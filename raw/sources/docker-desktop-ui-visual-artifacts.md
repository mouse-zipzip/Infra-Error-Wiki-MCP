# Docker Desktop UI가 녹색/왜곡/아티팩트로 표시됨

## 발생한 오류

Docker Desktop 앱을 열었을 때 UI가 아래 중 하나로 나타남:

- 화면 전체가 녹색으로 덮임
- UI 요소가 왜곡되거나 깨져서 보임
- 잔상(artifact)이 남거나 렌더링이 제대로 되지 않음

에러 메시지는 출력되지 않으며 시각적 증상으로만 확인됨.

## 당시 상황

- Docker Desktop 설치 또는 업데이트 후 앱을 처음 실행할 때 발생
- 특정 GPU 드라이버 버전 또는 하드웨어에서 재현됨
- Windows 또는 Mac 환경 모두에서 발생 가능

## 확인한 내용

- 다른 앱의 UI는 정상적으로 표시되는지 확인 → Docker Desktop만 문제라면 하드웨어 가속 문제로 특정 가능
- Docker Desktop 재시작 후에도 동일 증상 지속 여부 확인
- GPU 드라이버 버전 확인

`settings-store.json` 파일 위치:

- **Mac:** `~/Library/Group Containers/group.com.docker/settings-store.json`
- **Windows:** `C:\Users\<사용자명>\AppData\Roaming\Docker\settings-store.json`
- **Linux:** `~/.docker/desktop/settings-store.json`

## 원인

Docker Desktop의 UI 렌더링에 사용되는 하드웨어 가속(GPU)이 특정 GPU 드라이버 또는 환경과 호환되지 않아 렌더링 오류 발생.

## 해결 방법

Docker Desktop을 완전히 종료한 후, `settings-store.json` 파일에 하드웨어 가속 비활성화 옵션을 추가함.

**1. Docker Desktop 완전 종료**

시스템 트레이에서 Docker Desktop → Quit Docker Desktop

**2. `settings-store.json` 파일 열기**

OS에 맞는 경로에서 파일을 텍스트 편집기로 열기.

**3. 다음 항목 추가 또는 수정:**

```json
{
  "disableHardwareAcceleration": true
}
```

기존 JSON 객체에 키-값 쌍을 추가하는 형태로 삽입.

**4. Docker Desktop 재시작**

재시작 후 UI가 정상적으로 표시되는지 확인.

## 재발 방지

- GPU 드라이버를 최신 버전으로 업데이트하면 하드웨어 가속을 다시 활성화할 수 있음 (옵션 제거 후 테스트)
- 가상화 환경(VDI, VM)에서 Docker Desktop을 사용하는 경우 하드웨어 가속 비활성화를 기본값으로 유지하는 것을 권장

## 참고

- https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/
