import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

REX_BUNDLE = "com.superlogical.rex"


class RexError(RuntimeError):
    """Raised when Rex cannot perform a named action."""


def executable() -> str:
    """Find Rex even when Talon does not inherit the terminal's PATH."""
    candidates = (
        shutil.which("rex"),
        str(
            Path.home()
            / "Library/Application Support/com.superlogical.rex/RexServer"
            / "Versions/Current/Rex Server.app/Contents/MacOS/rex"
        ),
        "/opt/homebrew/bin/rex",
        "/usr/local/bin/rex",
    )
    for candidate in candidates:
        if candidate and os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    raise RexError("Could not find the Rex executable")


class Rex:
    """Run named Rex actions, including actions defined in init.lua.

    With no client selector, Rex selects the sole connected app and reports an
    error if there is more than one. Pass a client label or ID to disambiguate.
    Actions operate on the app's focus, not the terminal that launched Talon.
    """

    def __init__(self, client: str = "", *, timeout: float = 2.0) -> None:
        self.client = client
        self.timeout = timeout

    def perform_action(
        self, action: str, arguments: dict[str, Any] | None = None
    ) -> Any:
        """Perform a named action with JSON arguments and return its result."""
        # rex do also accepts Lua paths and flags; this API is for names only.
        if (
            not action.strip()
            or action.startswith("-")
            or "/" in action
            or "\\" in action
            or action.endswith(".lua")
        ):
            raise ValueError("Expected a Rex action name, not a script or option")
        if arguments is not None and not isinstance(arguments, dict):
            raise ValueError("Rex action arguments must be a JSON object")

        return self.call("do", action, "--args", json.dumps(arguments or {}), "--json")

    def call(self, *arguments: str) -> Any:
        """Run a Rex CLI request that produces JSON, without inherited targeting."""
        command = [executable(), "--timeout", f"{self.timeout}s"]
        if self.client:
            command.extend(["-C", self.client])
        command.extend(arguments)
        description = " ".join(arguments[:2])

        # Do not let an inherited Rex terminal environment pin voice commands
        # to an old pane, session, client, or remote server.
        env = os.environ.copy()
        for key in ("REX_SESSION", "REX_BLOCK", "REX_CLIENT", "REX_SERVER"):
            env.pop(key, None)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
                env=env,
            )
        except subprocess.TimeoutExpired as error:
            # The action may already have run. Never retry automatically.
            raise RexError(
                f"Rex request {description!r} timed out; check the app before retrying"
            ) from error
        except OSError as error:
            raise RexError(f"Rex request {description!r} failed: {error}") from error

        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            raise RexError(f"Rex request {description!r} failed: {message}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RexError(
                f"Rex request {description!r} returned invalid JSON"
            ) from error
