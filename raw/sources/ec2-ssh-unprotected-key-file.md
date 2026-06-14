# EC2 SSH 연결 시 UNPROTECTED PRIVATE KEY FILE 경고

## 발생한 오류

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0777 for '.ssh/my_private_key.pem' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
bad permissions: ignore key: .ssh/my_private_key.pem
Permission denied (publickey).
```

## 당시 상황

- `.pem` 키 파일을 다운로드하거나 다른 곳에서 복사한 후 SSH 연결을 시도할 때 발생
- Windows에서 WSL이나 Git Bash 등을 통해 처음 SSH 연결을 시도할 때 발생
- 키 파일 권한이 `0777` 또는 그룹/기타 사용자에게 읽기/쓰기 권한이 있는 경우

## 확인한 내용

키 파일 현재 권한 확인:

```bash
ls -la ~/.ssh/my_private_key.pem
# -rwxrwxrwx 1 user user 1766 Jun 14 10:00 my_private_key.pem  ← 권한이 너무 넓음
# -r-------- 1 user user 1766 Jun 14 10:00 my_private_key.pem  ← 올바른 권한
```

SSH는 보안상 다른 사용자도 읽을 수 있는 키 파일은 의도적으로 무시함.

## 원인

SSH 클라이언트는 개인 키 파일에 소유자 외의 사용자(그룹 또는 기타)가 접근 가능한 권한(`0777`, `0755`, `0644` 등)이 설정되어 있으면 보안 위협으로 판단하여 해당 키를 사용하지 않음.

## 해결 방법

**Mac/Linux:**

```bash
chmod 400 ~/.ssh/my_private_key.pem
# 또는
chmod 0400 ~/.ssh/my_private_key.pem
```

이후 SSH 연결:

```bash
ssh -i ~/.ssh/my_private_key.pem ec2-user@<public-ip>
```

**Windows (PowerShell):**

```powershell
# 현재 경로로 이동
$path = "C:\Users\<사용자명>\.ssh\my_private_key.pem"

# 기존 권한 초기화
icacls.exe $path /reset

# 현재 사용자에게 읽기 권한만 부여
icacls.exe $path /GRANT:R "$($env:USERNAME):(R)"

# 상속된 권한 제거
icacls.exe $path /inheritance:r
```

또는 GUI로:
1. `.pem` 파일 우클릭 → 속성 → 보안 탭 → 고급
2. 상속 사용 안 함 → 모든 상속된 권한 제거
3. 추가 → 현재 사용자 선택 → 읽기 권한만 부여
4. 확인 → 적용

## 재발 방지

- `.pem` 파일을 다운로드하자마자 즉시 `chmod 400` 적용하는 것을 습관화
- 키 파일을 공유 폴더나 클라우드 스토리지에 저장하지 않음 (권한이 초기화될 수 있음)
- `.gitignore`에 `*.pem`을 추가하여 실수로 저장소에 커밋되지 않도록 함

## 참고

- https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstancesConnecting.html
