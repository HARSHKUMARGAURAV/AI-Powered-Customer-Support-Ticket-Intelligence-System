"""
Single-command startup for the whole system.

Usage:
    python run.py

Starts the FastAPI backend (uvicorn) and the Streamlit UI together, and
stops both cleanly on Ctrl+C. This satisfies the "single-command startup"
requirement without needing Docker.
"""
import os
import signal
import subprocess
import sys
import time

from app.core.config import API_HOST, API_PORT, STREAMLIT_PORT

PROCESSES: list[subprocess.Popen] = []


def start(cmd: list[str], env: dict) -> subprocess.Popen:
    print(f"$ {' '.join(cmd)}")
    return subprocess.Popen(cmd, env=env)


def shutdown(*_args):
    print("\nShutting down...")
    for p in PROCESSES:
        if p.poll() is None:
            p.terminate()
    for p in PROCESSES:
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
    sys.exit(0)


def main():
    env = os.environ.copy()
    env.setdefault("API_BASE_URL", f"http://127.0.0.1:{API_PORT}")

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    api_proc = start(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", API_HOST, "--port", str(API_PORT)],
        env,
    )
    PROCESSES.append(api_proc)

    time.sleep(2)  # give the API a moment to bind before the UI starts polling it

    ui_proc = start(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "ui/streamlit_app.py",
            "--server.port",
            str(STREAMLIT_PORT),
            "--server.headless",
            "true",
        ],
        env,
    )
    PROCESSES.append(ui_proc)

    print(f"\nAPI docs:      http://127.0.0.1:{API_PORT}/docs")
    print(f"Streamlit UI:  http://127.0.0.1:{STREAMLIT_PORT}\n")
    print("Press Ctrl+C to stop both.\n")

    while True:
        for p in PROCESSES:
            if p.poll() is not None:
                shutdown()
        time.sleep(1)


if __name__ == "__main__":
    main()
