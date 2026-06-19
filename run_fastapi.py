from pathlib import Path
import os
import subprocess
import sys


def main():
    project_root = Path(__file__).resolve().parent

    env = os.environ.copy()

    # Equivalent to running: PYTHONPATH=.
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(project_root)
        if not existing_pythonpath
        else str(project_root) + os.pathsep + existing_pythonpath
    )

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "fast_api.app_indicator.main:app",
        "--reload",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        *sys.argv[1:],
    ]

    raise SystemExit(subprocess.call(cmd, env=env, cwd=project_root))


if __name__ == "__main__":
    main()