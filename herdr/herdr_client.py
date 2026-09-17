import json
import os
import shutil
import subprocess
from typing import Any


class HerdrError(RuntimeError):
    """Raised when the Herdr CLI cannot return a valid response."""


def executable() -> str:
    """Find Herdr even when Talon's PATH does not include Homebrew."""
    candidates = (
        shutil.which("herdr"),
        "/opt/homebrew/bin/herdr",
        "/usr/local/bin/herdr",
    )
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise HerdrError("Could not find the Herdr executable")


def call(*arguments: str, timeout: float = 0.75) -> dict[str, Any]:
    """Run a Herdr command and return its decoded JSON object."""
    try:
        result = subprocess.run(
            [executable(), *arguments],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise HerdrError(f"Herdr command failed: {error}") from error

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise HerdrError(f"Herdr command failed: {message}")

    try:
        response = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        raise HerdrError("Herdr returned invalid JSON") from error
    if not isinstance(response, dict):
        raise HerdrError("Herdr returned an unexpected response")
    return response


def result_list(command: tuple[str, ...], key: str) -> list[dict[str, Any]]:
    """Return a named list from a Herdr result object."""
    try:
        values = call(*command)["result"][key]
    except (KeyError, TypeError) as error:
        raise HerdrError(f"Herdr did not return {key}") from error
    if not isinstance(values, list):
        raise HerdrError(f"Herdr did not return {key}")
    return values


def current_pane() -> dict[str, Any]:
    """Return Herdr's focused pane."""
    try:
        pane = call("pane", "current")["result"]["pane"]
    except (KeyError, TypeError) as error:
        raise HerdrError("Herdr did not return its focused pane") from error
    if not isinstance(pane, dict):
        raise HerdrError("Herdr did not return its focused pane")
    return pane


def process_info(pane_id: str) -> dict[str, Any]:
    """Return foreground process information for a pane."""
    try:
        info = call("pane", "process-info", "--pane", pane_id)["result"][
            "process_info"
        ]
    except (KeyError, TypeError) as error:
        raise HerdrError("Herdr did not return process information") from error
    if not isinstance(info, dict):
        raise HerdrError("Herdr did not return process information")
    return info
