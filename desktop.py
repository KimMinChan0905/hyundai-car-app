from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import webview

BASE_DIR = Path(__file__).resolve().parent
APP_FILE = BASE_DIR / "app.py"


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def run_embedded_server(port: int) -> None:
    from streamlit.web import bootstrap

    flags = {
        "server_port": port,
        "server_address": "127.0.0.1",
        "server_headless": True,
        "global_developmentMode": False,
        "browser_gatherUsageStats": False,
        "server_fileWatcherType": "none",
    }
    bootstrap.load_config_options(flags)
    bootstrap.run(
        str(APP_FILE), False, [], flags
    )


def main() -> None:
    if not APP_FILE.exists():
        raise FileNotFoundError(f"앱 파일을 찾을 수 없습니다: {APP_FILE}")

    if len(sys.argv) >= 3 and sys.argv[1] == "--streamlit-server":
        run_embedded_server(int(sys.argv[2]))
        return

    port = find_free_port()
    log_path = BASE_DIR / "desktop_startup.log"
    with log_path.open("w", encoding="utf-8") as log_file:
        server = None
        if getattr(sys, "frozen", False):
            server = subprocess.Popen(
                [sys.executable, "--streamlit-server", str(port)],
                cwd=str(BASE_DIR), stdout=log_file, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        else:
            command = [
                sys.executable, "-m", "streamlit", "run", str(APP_FILE),
                f"--server.port={port}", "--server.address=127.0.0.1",
                "--server.headless=true", "--browser.gatherUsageStats=false",
                "--server.fileWatcherType=none",
            ]
            server = subprocess.Popen(
                command, cwd=str(BASE_DIR), stdout=log_file,
                stderr=subprocess.STDOUT, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0)
            )
        url = f"http://127.0.0.1:{port}"
        try:
            for _ in range(120):
                if server is not None and server.poll() is not None:
                    raise RuntimeError(f"Streamlit 실행 실패. 로그를 확인하세요: {log_path}")
                try:
                    with urllib.request.urlopen(url, timeout=1):
                        break
                except Exception:
                    time.sleep(0.25)
            else:
                raise TimeoutError(f"앱 서버 시작 시간이 초과되었습니다. 로그: {log_path}")

            webview.create_window(
                "현대자동차 앱 개발", url, width=1450, height=920,
                min_size=(1000, 650), text_select=True
            )
            webview.start()
        finally:
            if server is not None and server.poll() is None:
                server.terminate()
                try:
                    server.wait(timeout=6)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait(timeout=3)


if __name__ == "__main__":
    main()
