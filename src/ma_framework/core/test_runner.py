import subprocess
import sys
from pathlib import Path

from ma_framework.core.models import PytestResult


def run_pytest(
    run_id: str,
    module_filename: str,
    module_code: str,
    test_filename: str,
    test_code: str,
) -> PytestResult:
    """
    Writes module + tests under generated/work/<run_id>/ and runs pytest there.
    Returns stdout/stderr and pass/fail.
    """
    work_dir = Path("generated") / "work" / run_id
    work_dir.mkdir(parents=True, exist_ok=True)

    module_path = work_dir / module_filename
    test_path = work_dir / test_filename

    module_path.write_text(module_code, encoding="utf-8")
    test_path.write_text(test_code, encoding="utf-8")

    cmd = [sys.executable, "-m", "pytest", "-q"]
    proc = subprocess.run(
        cmd,
        cwd=str(work_dir),
        capture_output=True,
        text=True,
    )

    return PytestResult(
        passed=(proc.returncode == 0),
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )