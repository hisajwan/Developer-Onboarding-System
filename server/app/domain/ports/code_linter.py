from typing import Protocol, runtime_checkable

from app.domain.models import LintMessage


@runtime_checkable
class CodeLinter(Protocol):
    """Static analysis of one standalone snippet (no project, no import resolution)."""

    async def lint(self, code: str, filename: str) -> list[LintMessage]: ...
