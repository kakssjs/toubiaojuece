from pathlib import Path
import shutil
import subprocess
import sys


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


def run(command):
    subprocess.run(command, cwd=BASE_DIR, check=True)


def main():
    npm_command = shutil.which("npm") or shutil.which("npm.cmd")
    if npm_command is None:
        raise RuntimeError("npm is required to build the Vue frontend for Vercel.")

    run([npm_command, "ci", "--prefix", str(FRONTEND_DIR)])
    run([npm_command, "run", "build", "--prefix", str(FRONTEND_DIR)])
    run([sys.executable, "manage.py", "collectstatic", "--noinput"])


if __name__ == "__main__":
    main()
