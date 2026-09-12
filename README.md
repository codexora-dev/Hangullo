# Hangullo v0.0.1-beta

Hangullo는 한국어 키워드로 작성하고 Python 코드로 변환해 실행하는 작은 프로그래밍 언어입니다. 현재 버전은 Lexer -> Parser -> AST -> Python Code Generator 흐름을 제공하는 beta 버전입니다.

## 특징

- 한글과 영문 식별자
- 변수, 입출력, 조건문, 반복문, 함수와 반환
- `아니고만약`을 포함한 조건 분기
- 콜론과 들여쓰기를 사용하는 블록 문법
- 산술, 비교, 논리 연산
- `.hg` 파일과 CLI 실행

## 설치

Python 3.10 이상을 준비합니다. 핵심 컴파일러와 CLI는 Python 표준 라이브러리만 사용합니다.

```powershell
git clone https://github.com/codexora-dev/Hangullo.git
cd Hangullo
```

IDE를 빌드하려면 선택적으로 `requirements-ide.txt`를 설치합니다.

## 첫 번째 프로그램

```hangullo
출력("Hello, Hangullo!")
```

## 실행

```powershell
python main.py examples/01_hello.hg
python main.py examples/01_hello.hg --실행
```

첫 번째 명령은 생성된 Python 코드를 출력하고, 두 번째 명령은 프로그램을 실행합니다.

## 기본 문법

```hangullo
변수 이름 = "Hangullo"
출력(이름)

입력(이름, "이름을 입력하세요: ")

만약 점수 >= 90:
    출력("A")
아니고만약 점수 >= 80:
    출력("B")
아니면:
    출력("C")

반복 3:
    출력("반복")

함수 더하기(가, 나):
    반환 가 + 나

변수 결과 = 더하기(3, 5)
출력(결과)
```

블록은 콜론 뒤의 들여쓰기 구간으로 구분합니다. 별도의 `끝` 키워드는 사용하지 않습니다. 주석은 `#` 또는 `//`로 시작합니다.

## 예제

실행 가능한 예제는 [examples](examples)에서 확인할 수 있습니다.

- `01_hello.hg`: 출력
- `02_variables_and_math.hg`: 변수와 산술 연산
- `03_input_greeting.hg`: 입력
- `04_condition.hg`: 조건문
- `05_repeat.hg`: 반복문
- `06_function.hg`: 함수
- `07_logic_and_comparison.hg`: 비교와 논리
- `08_menu_program.hg`: 중첩 블록

## 프로젝트 구조

- `lexer/`: 소스 코드를 토큰으로 변환
- `parser/`: 토큰을 AST로 변환
- `compiler/`: AST를 Python 코드로 변환
- `runtime/`: 향후 런타임 확장을 위한 공간
- `IDE/`: Tkinter 기반 편집기
- `tests/`: Lexer, Parser, Code Generator, CLI 테스트
- `docs/`: 문법과 설계 문서
- `main.py`: CLI 진입점
- `errors.py`: Lexer, Parser, Compiler, Runtime 오류 형식

## 개발 및 테스트

```powershell
python -m unittest discover -s tests -v
```

## 버전과 제한

`v0.0.1-beta`는 작동 가능한 핵심 언어 흐름에 초점을 둔 beta 버전입니다. 자체 VM, 바이트코드, 패키지 관리자, 복잡한 표준 라이브러리, 고급 객체지향 기능은 아직 지원하지 않습니다.

## 로드맵

- 표준 라이브러리 설계
- 더 풍부한 런타임 오류 위치 연결
- 패키징과 배포 자동화
- IDE 기능 개선

## 라이선스

저장소의 라이선스 파일과 GitHub 저장소 정보를 기준으로 확인해 주세요.
