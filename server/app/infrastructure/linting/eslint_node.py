"""CodeLinter adapter: runs ESLint through the small Node helper in `server/lint/`.

ESLint is a Node library and this backend is Python, so each lint is one short subprocess: the
snippet goes in as JSON on stdin and the messages come back as JSON on stdout. No network.
"""

import asyncio
import json
from pathlib import Path

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, LinterError
from app.domain.models import LintMessage

_SCRIPT = "lint-snippet.mjs"


class EslintNodeLinter:
    def __init__(self, lint_dir: Path, *, node_binary: str = "node", timeout: float = 20.0) -> None:
        self._lint_dir = lint_dir
        self._node_binary = node_binary
        self._timeout = timeout

    @classmethod
    def from_settings(cls, settings: Settings) -> "EslintNodeLinter":
        return cls(
            settings.lint_dir,
            node_binary=settings.node_binary,
            timeout=settings.lint_timeout_seconds,
        )

    async def lint(self, code: str, filename: str) -> list[LintMessage]:
        self._check_installed()
        payload = json.dumps({"code": code, "filename": filename}).encode()
        try:
            process = await asyncio.create_subprocess_exec(
                self._node_binary,
                _SCRIPT,
                cwd=self._lint_dir,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
        except FileNotFoundError:
            raise ConfigurationError(
                f"Node.js ('{self._node_binary}') is needed for code review but was not found."
            ) from None

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(payload), timeout=self._timeout
            )
        except TimeoutError:
            process.kill()
            await process.wait()
            raise LinterError("Linting the snippet took too long.") from None

        if process.returncode != 0:
            raise LinterError(f"The linter failed: {_error_line(stderr)}")
        return _parse(stdout)

    def _check_installed(self) -> None:
        if not (self._lint_dir / _SCRIPT).is_file() or not (
            self._lint_dir / "node_modules"
        ).is_dir():
            raise ConfigurationError(
                "The code review linter is not installed: run `npm install` in server/lint."
            )


def _error_line(stderr: bytes) -> str:
    """The line naming the error; Node ends a crash with its own version line, not the cause."""
    lines = [line.strip() for line in stderr.decode(errors="replace").splitlines() if line.strip()]
    return next((line for line in lines if "Error" in line), lines[0] if lines else "no output")


def _parse(stdout: bytes) -> list[LintMessage]:
    try:
        raw = json.loads(stdout)["messages"]
        return [
            LintMessage(
                rule_id=item["rule_id"],
                message=item["message"],
                line=item["line"],
                column=item["column"],
                severity=item["severity"],
            )
            for item in raw
        ]
    except (ValueError, KeyError, TypeError):
        raise LinterError("The linter returned output that could not be read.") from None
