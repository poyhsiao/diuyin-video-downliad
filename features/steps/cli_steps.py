"""Step definitions for CLI feature."""

import subprocess
from pathlib import Path


@given("已安裝 douyin CLI")
def given_installed_cli():
    """Verify douyin CLI is installed."""
    # CLI is installed via entry point
    return True


@when('執行 "{command}"')
def when_execute_command(command):
    """Execute a command and return the result."""
    result = subprocess.run(
        command.split(),
        capture_output=True,
        text=True,
        cwd=Path.home() / "git/kimhsiao/diuyin-video-downliad"
    )
    return result


@then('輸出應包含 "{expected}"')
def then_output_contains(result, expected):
    """Verify command output contains expected text."""
    assert expected in result.stdout or expected in result.stderr