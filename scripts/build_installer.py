from __future__ import annotations

import argparse
import os
import platform
import plistlib
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from version import __version__


def find_inno_compiler() -> Path | None:
    configured_path = os.environ.get("INNO_SETUP_COMPILER")
    if configured_path and Path(configured_path).is_file():
        return Path(configured_path)

    located_path = shutil.which("ISCC.exe")
    if located_path:
        return Path(located_path)

    install_roots = (
        os.environ.get("ProgramFiles(x86)"),
        os.environ.get("ProgramFiles"),
        os.environ.get("LOCALAPPDATA"),
    )
    for install_root in install_roots:
        if install_root:
            candidate = Path(install_root) / "Inno Setup 6" / "ISCC.exe"
            if candidate.is_file():
                return candidate
    return None


def ensure_pyinstaller() -> None:
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(ROOT / "requirements-ide.txt")],
            cwd=ROOT,
            check=True,
        )


def clean_build_directories() -> None:
    build_root = ROOT / "build"
    for generated_dir in (
        build_root / "pyinstaller",
        build_root / "pyinstaller-work",
        build_root / "pyinstaller-spec",
        build_root / "macos-dmg",
    ):
        if generated_dir.exists():
            shutil.rmtree(generated_dir)


def configure_macos_bundle(app_bundle: Path) -> None:
    plist_path = app_bundle / "Contents" / "Info.plist"
    with plist_path.open("rb") as plist_file:
        info = plistlib.load(plist_file)

    bundle_version = __version__.removeprefix("v").split("-", 1)[0]
    info.update(
        {
            "CFBundleDisplayName": "Hangullo",
            "CFBundleIdentifier": "org.codexora.hangullo",
            "CFBundleShortVersionString": __version__.removeprefix("v"),
            "CFBundleVersion": bundle_version,
            "NSHighResolutionCapable": True,
            "UTExportedTypeDeclarations": [
                {
                    "UTTypeIdentifier": "org.codexora.hangullo-source",
                    "UTTypeDescription": "Hangullo source code",
                    "UTTypeConformsTo": ["public.plain-text"],
                    "UTTypeTagSpecification": {
                        "public.filename-extension": ["hg"]
                    },
                }
            ],
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Hangullo source file",
                    "CFBundleTypeRole": "Editor",
                    "LSHandlerRank": "Owner",
                    "LSItemContentTypes": ["org.codexora.hangullo-source"],
                    "CFBundleTypeExtensions": ["hg"],
                }
            ],
        }
    )
    with plist_path.open("wb") as plist_file:
        plistlib.dump(info, plist_file, sort_keys=False)


def build_application() -> Path:
    build_root = ROOT / "build"
    clean_build_directories()
    build_root.mkdir(parents=True, exist_ok=True)
    app_dist = build_root / "pyinstaller"
    work_dir = build_root / "pyinstaller-work"
    spec_dir = build_root / "pyinstaller-spec"

    icon_path = ROOT / "assets" / "icon" / "Hangullo_Logo2.ico"
    if sys.platform == "darwin":
        sips = shutil.which("sips")
        if not sips:
            raise RuntimeError("macOS 아이콘 변환 도구 sips를 찾을 수 없습니다.")
        icon_path = build_root / "Hangullo.icns"
        subprocess.run(
            [
                sips,
                "-s",
                "format",
                "icns",
                str(ROOT / "assets" / "icon" / "Hangullo_Logo1.png"),
                "--out",
                str(icon_path),
            ],
            check=True,
        )

    data_items = (
        (ROOT / "IDE" / "reserved_words.json", "IDE"),
        (ROOT / "assets", "assets"),
        (ROOT / "examples", "examples"),
        (ROOT / "docs", "docs"),
    )
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--name",
        "Hangullo",
        "--icon",
        str(icon_path),
        "--paths",
        str(ROOT),
        "--distpath",
        str(app_dist),
        "--workpath",
        str(work_dir),
        "--specpath",
        str(spec_dir),
    ]
    if sys.platform == "darwin":
        command.extend(("--osx-bundle-identifier", "org.codexora.hangullo"))

    for source, destination in data_items:
        if not source.exists():
            raise FileNotFoundError(f"패키징 리소스를 찾을 수 없습니다: {source}")
        command.extend(("--add-data", f"{source}{os.pathsep}{destination}"))
    command.extend(
        (
            "--collect-submodules",
            "compiler",
            "--collect-submodules",
            "lexer",
            "--collect-submodules",
            "parser",
            str(ROOT / "IDE" / "app.py"),
        )
    )
    subprocess.run(command, cwd=ROOT, check=True)

    if sys.platform == "darwin":
        app_bundle = app_dist / "Hangullo.app"
        if not app_bundle.is_dir():
            raise FileNotFoundError(f"macOS 앱 번들이 생성되지 않았습니다: {app_bundle}")
        configure_macos_bundle(app_bundle)
        return app_bundle

    executable = app_dist / "Hangullo" / "Hangullo.exe"
    if not executable.is_file():
        raise FileNotFoundError(f"실행 파일 생성에 실패했습니다: {executable}")
    return executable.parent


def build_macos_dmg(app_bundle: Path) -> Path:
    hdiutil = shutil.which("hdiutil")
    if not hdiutil:
        raise RuntimeError("macOS 디스크 이미지 도구 hdiutil을 찾을 수 없습니다.")

    staging_root = ROOT / "build" / "macos-dmg"
    staging_root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(app_bundle, staging_root / "Hangullo.app", symlinks=True)
    (staging_root / "Applications").symlink_to("/Applications", target_is_directory=True)

    architecture = platform.machine().lower()
    if architecture not in {"arm64", "x86_64"}:
        raise RuntimeError(f"지원하지 않는 macOS 빌드 아키텍처입니다: {architecture}")
    dmg_path = ROOT / "dist" / f"Hangullo-v{__version__}-macOS-{architecture}.dmg"
    (ROOT / "dist").mkdir(exist_ok=True)
    subprocess.run(
        [
            hdiutil,
            "create",
            "-volname",
            "Hangullo",
            "-srcfolder",
            str(staging_root),
            "-ov",
            "-format",
            "UDZO",
            str(dmg_path),
        ],
        check=True,
    )
    return dmg_path


def main() -> int:
    parser = argparse.ArgumentParser(description="현재 OS용 Hangullo 배포 파일을 빌드합니다.")
    parser.add_argument(
        "--app-only",
        action="store_true",
        help="Inno Setup이 없어도 PyInstaller 실행 파일만 빌드합니다.",
    )
    args = parser.parse_args()

    if sys.platform not in {"win32", "darwin"}:
        print("Windows 또는 macOS에서 실행해야 합니다.", file=sys.stderr)
        return 2

    is_macos = sys.platform == "darwin"
    compiler = None if args.app_only or is_macos else find_inno_compiler()
    if not args.app_only and not is_macos and compiler is None:
        print(
            "Inno Setup 6을 찾을 수 없습니다. 설치 후 다시 실행하거나 "
            "INNO_SETUP_COMPILER 환경 변수로 ISCC.exe 경로를 지정하세요.",
            file=sys.stderr,
        )
        return 2

    try:
        ensure_pyinstaller()
        payload_dir = build_application()
        if args.app_only:
            print(f"앱 빌드 완료: {payload_dir}")
            return 0

        if is_macos:
            dmg_path = build_macos_dmg(payload_dir)
            print(f"macOS 디스크 이미지 빌드 완료: {dmg_path}")
            return 0

        (ROOT / "dist").mkdir(exist_ok=True)
        subprocess.run(
            [
                str(compiler),
                f"/DAppVersion={__version__}",
                f"/DProjectDir={ROOT}",
                f"/DPayloadDir={payload_dir}",
                str(ROOT / "installer" / "Hangullo.iss"),
            ],
            cwd=ROOT,
            check=True,
        )
    except (OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"빌드 실패: {error}", file=sys.stderr)
        return 1

    installer = ROOT / "dist" / f"Hangullo-v{__version__}-Setup.exe"
    if not installer.is_file():
        print(f"설치 파일 생성에 실패했습니다: {installer}", file=sys.stderr)
        return 1
    print(f"설치 프로그램 빌드 완료: {installer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())