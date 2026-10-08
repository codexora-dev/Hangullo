# Supabase 설정 및 배포

## 클라이언트 설정

IDE는 Python 표준 라이브러리의 HTTPS 요청만 사용하므로 추가 패키지가 필요하지 않습니다. `requirements-ide.txt`는 기존 PyInstaller 의존성만 유지합니다.

개발 실행에서는 다음 PowerShell 환경 변수를 설정합니다.

```powershell
$env:HANGULLO_SUPABASE_URL = "https://<project-ref>.supabase.co"
$env:HANGULLO_SUPABASE_ANON_KEY = "<publishable-or-anon-key>"
python IDE/app.py
```

배포 빌드에서는 `IDE/supabase_config.py`의 두 빈 설정값에 Supabase project URL과 publishable/anon key를 입력한 뒤 빌드합니다. 이 모듈은 앱에 포함됩니다. 환경 변수는 설정 파일 값보다 우선합니다. publishable/anon key는 클라이언트 공개용이며 RLS 정책으로 권한을 제한해야 합니다. **service_role 키는 코드, 환경 변수, 빌드 결과 어디에도 넣지 마세요.**

두 값이 설정되지 않았거나 네트워크가 실패하면 피드백 제출은 재시도 안내를 표시하고, 업데이트 확인은 건너뜁니다. IDE 실행은 계속 가능합니다. 요청 timeout은 8초입니다.

## 테이블과 RLS

Supabase SQL Editor에서 [`supabase/schema.sql`](../supabase/schema.sql)을 실행합니다. 이 스키마는 다음을 생성합니다.

- `usage_surveys`, `experience_surveys`, `bug_reports`, `feature_requests`: 익명 역할에 INSERT만 허용
- `app_updates`: 공개된 업데이트에 대해서만 SELECT 허용, 읽기 컬럼은 버전·다운로드 주소·릴리스 노트·필수 여부·게시 시간으로 제한
- 모든 테이블에 RLS 활성화, 익명 역할의 SELECT/UPDATE/DELETE 권한 없음

오류 로그는 사용자가 직접 입력하고 체크한 경우에만 `bug_reports.error_log`로 보냅니다. 프로그램은 프로젝트 코드, 파일, 컴퓨터 이름, 계정명, MAC 주소, 이름, 이메일, 전화번호를 자동 수집하지 않습니다.

## 업데이트 게시

설치 파일은 기존 `scripts/build_installer.py`와 Inno Setup 절차로 생성합니다. 완성한 `Hangullo-v<version>-Setup.exe`를 GitHub 저장소 `codexora-dev/Hangullo`의 Release asset으로 올립니다. Supabase Storage에는 설치 파일을 올리지 않습니다.

그 후 `app_updates`에 새 버전 행을 추가합니다. `download_url`은 다음 저장소의 GitHub Release 다운로드 URL이어야 합니다.

```text
https://github.com/codexora-dev/Hangullo/releases/download/<tag>/<installer-file>
```

클라이언트는 HTTPS의 해당 저장소 Release 경로만 열도록 검증합니다. 앱이 설치 프로그램을 자체 덮어쓰지 않고 사용자의 확인 후 Release 페이지를 엽니다. Inno Setup은 기존 설치 경로에 설치하고 사용자 설정은 `%APPDATA%\Hangullo`, 프로젝트는 Documents 아래에 두므로 앱 업데이트/재설치 시 해당 데이터가 제거되지 않습니다. 다운로드/설치 실패 시 기존 앱을 자동 삭제하거나 수정하지 않습니다.

## 로컬 검증

```powershell
python -m unittest tests.test_supabase_client tests.test_update_checker -v
python -m unittest discover -s tests -v
```

백엔드 연결 전에는 빈 환경 변수 상태에서 IDE를 실행해 첫 실행 설문에서 `나중에 하기`를 선택하고 편집/실행/종료가 되는지 확인합니다. Supabase project URL과 anon key를 설정한 뒤 각 설문 및 폼을 제출하고 테이블에 응답이 추가되는지 확인합니다. 네트워크 요청을 차단한 상태에서도 IDE가 시작되는지 확인합니다.

## Windows 배포 검증

Python이 없는 Windows 10/11 x64 환경에서 공개 설정이 포함된 설치 파일을 설치합니다. 첫 설문 취소/나중에 하기, 각 피드백 폼 입력 검증 및 제출, 오프라인 시작, 업데이트 알림의 나중에/업데이트 동작을 확인합니다. 설치 위치에 기존 버전이 있는 상태에서 Release 설치 프로그램을 실행해 설정과 Documents 프로젝트가 보존되는지 확인합니다. 이 환경의 IDE 실행/네트워크/설치 테스트는 현재 개발 PC에서 자동으로 확인되지 않았습니다.

## 배포 전 운영 설정

- Supabase 프로젝트 생성 후 이 저장소의 SQL 적용
- project URL과 publishable/anon key 설정, RLS 정책 실제 적용 상태 점검
- `version.py` 변경 후 설치 프로그램을 GitHub Release에 게시
- Release URL 및 업데이트 행의 버전/노트/필수 여부 등록
- GitHub Actions artifact만으로는 Release 게시가 되지 않으므로 Release asset 업로드 수행
- 사용자 데이터의 보관 기간 및 삭제 요청 대응 절차 결정