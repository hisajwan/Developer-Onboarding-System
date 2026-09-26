"""Reads a pasted unified diff (`git diff` output) into files, hunks and changed lines.

Each hunk is rebuilt as the new version of that part of the file (context plus added lines), with
every rebuilt line mapped to its line number in the new file and marked if it was added, so lint
results on the rebuilt code can be traced back to changed lines only.
"""

import re
from dataclasses import dataclass, field
from pathlib import PurePosixPath

_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
_REVIEWABLE = {".js": "js", ".jsx": "jsx", ".ts": "ts", ".tsx": "tsx"}


@dataclass
class Hunk:
    new_start: int
    code_lines: list[str] = field(default_factory=list)  # the new side: context + added
    new_line_numbers: list[int] = field(default_factory=list)
    added: list[bool] = field(default_factory=list)

    @property
    def code(self) -> str:
        return "\n".join(self.code_lines)

    def added_line(self, rebuilt_line: int) -> int | None:
        """The new-file line number of a rebuilt line (1-based), if that line was added."""
        index = rebuilt_line - 1
        if 0 <= index < len(self.code_lines) and self.added[index]:
            return self.new_line_numbers[index]
        return None


@dataclass
class DiffFile:
    path: str
    hunks: list[Hunk] = field(default_factory=list)

    @property
    def language(self) -> str | None:
        """The snippet language ESLint should use, or None for files the review doesn't cover."""
        return _REVIEWABLE.get(PurePosixPath(self.path).suffix.lower())


def looks_like_diff(text: str) -> bool:
    lines = text.lstrip().splitlines()
    has_hunk = any(_HUNK_HEADER.match(line) for line in lines)
    has_header = any(line.startswith(("diff --git", "+++ ", "--- ")) for line in lines)
    return has_hunk and has_header


def parse_diff(text: str) -> list[DiffFile]:
    files: list[DiffFile] = []
    current: DiffFile | None = None
    hunk: Hunk | None = None
    next_line = 0
    for raw in text.splitlines():
        if raw.startswith("diff --git"):
            current, hunk = None, None
        elif raw.startswith("+++ "):
            path = raw[4:].strip()
            path = path[2:] if path.startswith("b/") else path
            current = DiffFile(path=path)
            files.append(current)
            hunk = None
        elif raw.startswith("--- "):
            continue
        elif (match := _HUNK_HEADER.match(raw)) and current is not None:
            next_line = int(match.group(1))
            hunk = Hunk(new_start=next_line)
            current.hunks.append(hunk)
        elif hunk is not None and raw[:1] in ("+", " ", ""):
            hunk.code_lines.append(raw[1:])
            hunk.new_line_numbers.append(next_line)
            hunk.added.append(raw.startswith("+"))
            next_line += 1
        # "-" lines (removed) and "\ No newline at end of file" are not part of the new code.
    return [f for f in files if f.path != "/dev/null" and f.hunks]
