from __future__ import annotations

import socket
import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"


def local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def main() -> None:
    if not APP_FILE.exists():
        raise FileNotFoundError(f"앱 파일을 찾을 수 없습니다: {APP_FILE}")

    ip = local_ip()
    port = 8502
    print("현대자동차 앱 개발 모바일 접속 서버를 시작합니다.")
    print(f"이 컴퓨터: http://localhost:{port}")
    print(f"스마트폰: http://{ip}:{port}")
    print("스마트폰과 컴퓨터가 같은 Wi-Fi에 연결되어 있어야 합니다.")
    print("종료하려면 Ctrl+C를 누르세요.")

    command = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(APP_FILE),
        f"--server.port={port}",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--server.fileWatcherType=none",
    ]
    subprocess.run(command, cwd=str(BASE_DIR), check=False)


if __name__ == "__main__":
    main()
