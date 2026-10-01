# Windows 및 macOS 배포

Windows 배포본은 PyInstaller `onedir` 실행 파일과 Inno Setup 6 설치 마법사로 만듭니다. macOS 배포본은 PyInstaller `.app` 번들과 압축 DMG로 만듭니다. 두 빌드 모두 Python 런타임, Tkinter, IDE 리소스를 함께 포함하므로 최종 사용자는 Python이나 개발 도구를 설치할 필요가 없습니다.

## Windows 빌드

빌드 PC에는 Windows x64, Python 3.10 이상, Inno Setup 6이 필요합니다. PyInstaller가 없으면 빌드 스크립트가 `requirements-ide.txt`를 사용해 설치합니다.

```bat
build_installer.bat
```

Inno Setup을 기본 경로가 아닌 곳에 설치했다면 `INNO_SETUP_COMPILER`에 `ISCC.exe` 전체 경로를 지정합니다. 설치 프로그램 없이 실행 파일만 점검할 때는 다음 명령을 사용합니다.

```bat
python scripts\build_installer.py --app-only
```

설치 파일은 `dist\Hangullo-v0.0.1-beta-Setup.exe`에 생성됩니다. 빌드는 자체 `build\pyinstaller*` 폴더만 다시 만들며 기존 `dist`의 다른 파일은 지우지 않습니다.

## macOS 빌드

빌드 PC에는 macOS, Python 3.10 이상, Xcode Command Line Tools의 `sips`와 `hdiutil`이 필요합니다. 스크립트는 현재 Mac의 CPU 아키텍처에 맞춰 빌드합니다.

```sh
python scripts/build_installer.py
```

결과는 `dist/Hangullo-v0.0.1-beta-macOS-arm64.dmg` 또는 `dist/Hangullo-v0.0.1-beta-macOS-x86_64.dmg`입니다. DMG를 열고 `Hangullo.app`을 Applications 폴더로 드래그합니다. `.hg` 파일 형식은 앱 번들에 등록됩니다. 코드 서명·Apple 공증은 포함하지 않아 외부 배포 시 Gatekeeper 경고가 표시될 수 있습니다.

현재 macOS에서는 설정이 `~/Library/Application Support/Hangullo`에, 프로젝트와 예제가 `~/Documents/Hangullo`에 저장됩니다.

## 설치 동작

- 기본 경로: `%LOCALAPPDATA%\Programs\Hangullo`이며 설치 위치를 변경할 수 있습니다.
- 설치 및 `.hg` 파일 연결은 현재 사용자 범위로 등록되며 관리자 권한을 요구하지 않습니다.
- 시작 메뉴 바로가기는 기본 생성되고, 바탕 화면 바로가기와 `.hg` 연결은 설치 옵션에서 선택합니다.
- 설정은 `%APPDATA%\Hangullo\settings.json`에 저장됩니다. 작업 폴더와 예제는 `%USERPROFILE%\Documents\Hangullo`에 놓입니다.
- 제거 프로그램은 설치 파일과 설치 바로가기/파일 연결을 제거합니다. 문서 폴더의 프로젝트, 예제 수정본, 설정은 삭제하지 않습니다.

## 깨끗한 Windows 설치 테스트

- [ ] Python이 설치되지 않은 Windows 10/11 x64 PC에서 설치 파일 실행
- [ ] 설치 위치 변경 후 설치와 시작 메뉴 실행
- [ ] 바탕 화면 바로가기 선택 및 실행
- [ ] `.hg` 파일 연결 선택 후 탐색기에서 더블클릭해 파일 열기
- [ ] 새 파일 만들기, 편집, 저장, 다시 열기
- [ ] 텍스트 모드와 블록 모드 전환 및 저장
- [ ] F5 실행, 콘솔 출력, `입력` 값 입력, 실행 중지
- [ ] F6 컴파일 및 오류가 있는 코드의 오류 메시지 확인
- [ ] 테마와 설정 변경 후 앱 재실행해 유지되는지 확인
- [ ] 설정 > 앱에서 제거한 뒤 사용자 프로젝트와 `.hg` 파일이 남는지 확인

GUI 입력/중지와 설치 후 제거 동작은 깨끗한 Windows 환경에서 수동 확인해야 합니다. 빌드 성공만으로 이 동작들이 검증되는 것은 아닙니다.

## GitHub 배포

`v*` 태그 또는 Actions의 수동 실행으로 Windows 설치 파일과 Apple Silicon·Intel Mac 디스크 이미지를 각각 빌드해 Actions artifact로 올립니다. Release 게시까지 자동화하려면 이후 별도의 권한 범위와 배포 절차를 정해 `contents: write` 권한 및 GitHub Release 업로드 단계를 추가합니다.