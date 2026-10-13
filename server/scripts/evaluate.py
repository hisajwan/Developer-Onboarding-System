"""Runs a question set and/or a snippet set against one project and writes the results as CSV.

Questions go through the same agent as Ask mode (no chat history); snippets through the same
reviewer as the Code review screen. Nothing is saved to the project's chat history or dashboard.
Uses the providers configured in server/.env; if any is not `fake`, it asks before calling them.

Run from server/, with the venv active:
    python scripts/evaluate.py --owner dev --project "My Project" \
        --questions questions.json --snippets snippets.json --out results/ --pause 5

questions.json: [{"id": "q1", "question": "...", "expected_sources": ["setup.md"]}, ...]
snippets.json:  [{"id": "s1", "code": "...", "language": "tsx",
                  "expected_categories": ["accessibility"]}, ...]
`expected_*` are optional. See scripts/evaluation-examples/ for small samples.
"""

import argparse
import asyncio
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.api.container import Container  # noqa: E402
from app.core.config import Settings, get_settings  # noqa: E402
from app.domain.models import Project  # noqa: E402
from app.services.evaluation_service import QuestionCase, SnippetCase  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--owner", required=True, help="username that owns the project")
    parser.add_argument("--project", required=True, help="project name or id")
    parser.add_argument("--questions", type=Path, help="JSON list of question cases")
    parser.add_argument("--snippets", type=Path, help="JSON list of snippet cases")
    parser.add_argument("--out", type=Path, default=Path("evaluation-results"))
    parser.add_argument(
        "--pause", type=float, default=0.0, help="seconds between cases (stay under rate limits)"
    )
    parser.add_argument("--yes", action="store_true", help="don't ask before real provider calls")
    args = parser.parse_args()
    if not (args.questions or args.snippets):
        parser.error("give --questions, --snippets or both")
    return args


def load_questions(path: Path) -> list[QuestionCase]:
    return [
        QuestionCase(
            id=str(item["id"]),
            question=item["question"],
            expected_sources=tuple(item.get("expected_sources", ())),
        )
        for item in json.loads(path.read_text())
    ]


def load_snippets(path: Path) -> list[SnippetCase]:
    return [
        SnippetCase(
            id=str(item["id"]),
            code=item["code"],
            language=item.get("language", "tsx"),
            expected_categories=tuple(item.get("expected_categories", ())),
        )
        for item in json.loads(path.read_text())
    ]


async def find_project(container: Container, owner: str, name_or_id: str) -> Project:
    projects = await container.project_registry.list_for_owner(owner)
    matches = [p for p in projects if name_or_id in (p.id, p.name)]
    if len(matches) != 1:
        found = ", ".join(f"{p.name} ({p.id})" for p in projects) or "none"
        sys.exit(f"Expected one project '{name_or_id}' owned by {owner}; their projects: {found}")
    return matches[0]


def confirm_real_providers(settings: Settings, assume_yes: bool) -> None:
    providers = {
        "LLM": settings.llm_provider,
        "embeddings": settings.embedding_provider,
    }
    print("Providers: " + ", ".join(f"{kind}={name}" for kind, name in providers.items()))
    if assume_yes or all(name == "fake" for name in providers.values()):
        return
    if input("This calls real model providers and uses quota. Continue? [y/N] ").lower() != "y":
        sys.exit("Cancelled.")


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {path}")


async def main() -> None:
    args = parse_args()
    settings = get_settings()
    confirm_real_providers(settings, args.yes)

    container = Container(settings)
    project = await find_project(container, args.owner, args.project)
    service = container.evaluation_service_for(project.id)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    args.out.mkdir(parents=True, exist_ok=True)

    async def pause(index: int) -> None:
        if index and args.pause:
            await asyncio.sleep(args.pause)

    if args.questions:
        rows = []
        for index, case in enumerate(load_questions(args.questions)):
            await pause(index)
            result = await service.ask(case)
            print(f"  {case.id}: {result.cost.seconds}s, {result.cost.total_calls} calls"
                  + (f", error: {result.error}" if result.error else ""))
            rows.append(result.to_row())
        write_csv(args.out / f"questions-{stamp}.csv", rows)

    if args.snippets:
        rows = []
        for index, case in enumerate(load_snippets(args.snippets)):
            await pause(index)
            result = await service.review(case)
            print(f"  {case.id}: {result.cost.seconds}s, {result.cost.total_calls} calls"
                  + (f", error: {result.error}" if result.error else ""))
            rows.append(result.to_row())
        write_csv(args.out / f"snippets-{stamp}.csv", rows)


if __name__ == "__main__":
    asyncio.run(main())
