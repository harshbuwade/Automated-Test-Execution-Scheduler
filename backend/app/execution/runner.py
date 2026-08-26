from datetime import datetime, timezone
import os
import subprocess
import sys
from typing import Any, Dict
from app.config import settings
from app.core.path_security import sanitize_and_validate_script_path
from app.models.enums import ExecutionStatus

# Output length limit (50,000 characters per stream) to prevent excessive DB record sizes
MAX_OUTPUT_LENGTH = 50000


def truncate_output(output_text: str) -> str:
    """Truncates output string if it exceeds MAX_OUTPUT_LENGTH."""
    if not output_text:
        return ""
    if len(output_text) > MAX_OUTPUT_LENGTH:
        truncated_part = output_text[:MAX_OUTPUT_LENGTH]
        return f"{truncated_part}\n... [Output truncated to {MAX_OUTPUT_LENGTH} characters]"
    return output_text


def find_repo_root() -> str:
    """Finds the root repository directory containing test_scripts or .git."""
    curr = os.path.dirname(os.path.abspath(__file__))
    while curr and os.path.dirname(curr) != curr:
        if os.path.exists(os.path.join(curr, settings.TEST_SCRIPTS_DIR)) or os.path.exists(os.path.join(curr, ".git")):
            return curr
        curr = os.path.dirname(curr)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def run_pytest_script(relative_script_path: str, timeout: int) -> Dict[str, Any]:
    """Safely executes a pytest test script in an isolated subprocess.

    Requirements:
    - shell=False strictly enforced.
    - Script path validated & resolved against workspace root.
    - Timeout enforced cleanly with process termination.
    - stdout/stderr captured and truncated.
    - Exit code mapped to ExecutionStatus (0 -> PASSED, non-zero -> FAILED, timeout -> TIMEOUT).

    Returns:
        Dict containing: status, exit_code, stdout, stderr, started_at, finished_at, duration.
    """
    # 1. Validate script path security & resolve path
    validated_rel_path = sanitize_and_validate_script_path(relative_script_path)

    # Repository root directory
    repo_root = find_repo_root()
    absolute_script_path = os.path.abspath(os.path.join(repo_root, validated_rel_path))

    started_at = datetime.now(timezone.utc)

    if not os.path.exists(absolute_script_path):
        return {
            "status": ExecutionStatus.FAILED,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Error: Test script file not found on disk at '{validated_rel_path}' (Resolved: {absolute_script_path}).",
            "started_at": started_at,
            "finished_at": started_at,
            "duration": 0.0,
        }


    finished_at = started_at
    duration = 0.0

    cmd = [sys.executable, "-m", "pytest", absolute_script_path]

    try:
        process = subprocess.Popen(

            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )

        stdout_data, stderr_data = process.communicate(timeout=timeout)
        finished_at = datetime.now(timezone.utc)
        duration = round((finished_at - started_at).total_seconds(), 4)
        exit_code = process.returncode

        if exit_code == 0:
            exec_status = ExecutionStatus.PASSED
        else:
            exec_status = ExecutionStatus.FAILED

        return {
            "status": exec_status,
            "exit_code": exit_code,
            "stdout": truncate_output(stdout_data),
            "stderr": truncate_output(stderr_data),
            "started_at": started_at,
            "finished_at": finished_at,
            "duration": duration,
        }

    except subprocess.TimeoutExpired:
        finished_at = datetime.now(timezone.utc)
        duration = round((finished_at - started_at).total_seconds(), 4)

        process.kill()
        partial_stdout, partial_stderr = process.communicate()

        timeout_stderr = (
            (partial_stderr or "")
            + f"\n[Execution Engine Timeout]: Test execution exceeded configured timeout limit of {timeout} seconds."
        )

        return {
            "status": ExecutionStatus.TIMEOUT,
            "exit_code": -1,
            "stdout": truncate_output(partial_stdout or ""),
            "stderr": truncate_output(timeout_stderr),
            "started_at": started_at,
            "finished_at": finished_at,
            "duration": duration,
        }
    except Exception as exc:
        finished_at = datetime.now(timezone.utc)
        duration = round((finished_at - started_at).total_seconds(), 4)
        return {
            "status": ExecutionStatus.FAILED,
            "exit_code": -1,
            "stdout": "",
            "stderr": f"Execution Engine Error: {str(exc)}",
            "started_at": started_at,
            "finished_at": finished_at,
            "duration": duration,
        }
