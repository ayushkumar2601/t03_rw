#!/usr/bin/env python3
"""Unified runner for Task 03: Company Knowledge Base RAG.

Spawns both the FastAPI backend and Next.js frontend concurrently in a single terminal,
streams their logs with color-coded prefixes, and handles clean shutdown on Ctrl+C.
"""

import os
import signal
import subprocess
import sys
import threading
from pathlib import Path
import shutil

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
VENV_BIN = ROOT_DIR / ".venv" / "bin"

# Terminal ANSI colors
CYAN = "\033[36m"
MAGENTA = "\033[35m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"

processes = []
shutting_down = False


def log_stream(pipe, prefix, color):
    """Read lines from a pipe and print them with a formatted prefix."""
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            line_str = line.rstrip()
            if line_str:
                print(f"{color}{BOLD}[{prefix}]{RESET} {line_str}", flush=True)
    except Exception:
        pass


def shutdown(signum=None, frame=None):
    """Gracefully terminate both processes and their process groups."""
    global shutting_down
    if shutting_down:
        return
    shutting_down = True
    print(f"\n{YELLOW}{BOLD}[Runner] Stopping backend and frontend...{RESET}", flush=True)

    for proc, name in processes:
        if proc.poll() is None:
            try:
                # Terminate entire process group
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                try:
                    proc.terminate()
                except Exception:
                    pass

    # Wait for processes to exit
    for proc, name in processes:
        try:
            proc.wait(timeout=3)
        except Exception:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass

    print(f"{GREEN}{BOLD}[Runner] Both services stopped cleanly.{RESET}", flush=True)
    sys.exit(0)


def free_ports(*ports):
    """Ensure specified ports are free before launching."""
    for port in ports:
        try:
            out = subprocess.check_output(["lsof", "-t", f"-i:{port}"], text=True).strip()
            if out:
                pids = [p for p in out.splitlines() if p.strip()]
                for pid in pids:
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                    except Exception:
                        pass
        except Exception:
            pass


def main():
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # 0. Free ports 8000 and 3000 if lingering from previous run
    free_ports(8000, 3000)

    # 1. Determine Python / Uvicorn executable
    if (VENV_BIN / "uvicorn").exists():
        uvicorn_bin = str(VENV_BIN / "uvicorn")
    else:
        uvicorn_bin = shutil.which("uvicorn") or sys.executable

    # 2. Determine npm executable
    npm_bin = shutil.which("npm")
    if not npm_bin:
        print(f"{RED}Error: 'npm' was not found on your PATH. Please install Node.js.{RESET}")
        sys.exit(1)

    print(f"{GREEN}{BOLD}======================================================{RESET}")
    print(f"{GREEN}{BOLD}    Starting Company Knowledge Base RAG Chatbot       {RESET}")
    print(f"{GREEN}{BOLD}======================================================{RESET}")
    print(f"{CYAN}  • Backend : http://127.0.0.1:8000 (Docs: http://127.0.0.1:8000/docs){RESET}")
    print(f"{MAGENTA}  • Frontend: http://localhost:3000{RESET}")
    print(f"{YELLOW}  • Press Ctrl+C at any time to shut down both.{RESET}\n")

    # 3. Start Backend
    backend_cmd = [
        uvicorn_bin if uvicorn_bin.endswith("uvicorn") else sys.executable,
        *([] if uvicorn_bin.endswith("uvicorn") else ["-m", "uvicorn"]),
        "main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload",
    ]

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid,
    )
    processes.append((backend_proc, "Backend"))

    # 4. Start Frontend
    frontend_cmd = [npm_bin, "run", "dev"]
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        cwd=str(FRONTEND_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid,
    )
    processes.append((frontend_proc, "Frontend"))

    # 5. Start logging threads
    threads = [
        threading.Thread(target=log_stream, args=(backend_proc.stdout, "BACKEND", CYAN), daemon=True),
        threading.Thread(target=log_stream, args=(backend_proc.stderr, "BACKEND", CYAN), daemon=True),
        threading.Thread(target=log_stream, args=(frontend_proc.stdout, "FRONTEND", MAGENTA), daemon=True),
        threading.Thread(target=log_stream, args=(frontend_proc.stderr, "FRONTEND", MAGENTA), daemon=True),
    ]

    for t in threads:
        t.start()

    # 6. Wait for any process to exit unexpectedly
    while not shutting_down:
        b_exit = backend_proc.poll()
        f_exit = frontend_proc.poll()

        if b_exit is not None:
            print(f"{RED}[Runner] Backend process exited unexpectedly with code {b_exit}.{RESET}")
            shutdown()
            break
        if f_exit is not None:
            print(f"{RED}[Runner] Frontend process exited unexpectedly with code {f_exit}.{RESET}")
            shutdown()
            break

        signal.pause()


if __name__ == "__main__":
    main()
