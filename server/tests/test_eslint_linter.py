from pathlib import Path

import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, LinterError
from app.domain.ports import CodeLinter
from app.infrastructure.linting.eslint_node import EslintNodeLinter
from tests.conftest import requires_linter

FLAWED = """function Card({ src, items }) {
  var x = 1;
  return <div><img src={src} />{items.map((i) => <p>{i}</p>)}</div>;
}"""

CLEAN = """export function Title({ text }: { text: string }) {
  return <h1>{text}</h1>;
}"""


def real_linter() -> EslintNodeLinter:
    return EslintNodeLinter.from_settings(Settings(_env_file=None))


def fake_helper(tmp_path: Path, script: str) -> Path:
    """A lint dir whose 'helper' is a tiny script, to test how the adapter handles bad output."""
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "lint-snippet.mjs").write_text(script)
    return tmp_path


def test_satisfies_the_code_linter_port() -> None:
    assert isinstance(real_linter(), CodeLinter)


@requires_linter
@pytest.mark.anyio
async def test_a_flawed_snippet_gets_accessibility_key_and_style_findings() -> None:
    messages = await real_linter().lint(FLAWED, "snippet.tsx")

    rules = {m.rule_id for m in messages}
    assert {"jsx-a11y/alt-text", "react/jsx-key", "no-var"} <= rules
    assert "@typescript-eslint/no-unused-vars" in rules  # x, not the capitalised Card
    assert all("'Card'" not in m.message for m in messages)
    alt = next(m for m in messages if m.rule_id == "jsx-a11y/alt-text")
    assert (alt.line, alt.severity) == (3, "error")


@requires_linter
@pytest.mark.anyio
async def test_a_clean_snippet_gets_no_findings() -> None:
    assert await real_linter().lint(CLEAN, "snippet.tsx") == []


@requires_linter
@pytest.mark.anyio
async def test_a_snippet_that_does_not_parse_comes_back_as_one_message_without_a_rule() -> None:
    [message] = await real_linter().lint("const = ;", "snippet.tsx")

    assert message.rule_id is None
    assert "Parsing error" in message.message


@pytest.mark.anyio
async def test_a_missing_install_is_a_configuration_error(tmp_path: Path) -> None:
    with pytest.raises(ConfigurationError, match="npm install"):
        await EslintNodeLinter(tmp_path).lint("x", "snippet.tsx")


@pytest.mark.anyio
async def test_a_missing_node_binary_is_a_configuration_error(tmp_path: Path) -> None:
    linter = EslintNodeLinter(fake_helper(tmp_path, ""), node_binary="no-such-node-binary")

    with pytest.raises(ConfigurationError, match="Node.js"):
        await linter.lint("x", "snippet.tsx")


@requires_linter
@pytest.mark.anyio
async def test_unreadable_helper_output_is_a_linter_error(tmp_path: Path) -> None:
    linter = EslintNodeLinter(fake_helper(tmp_path, 'process.stdout.write("not json");'))

    with pytest.raises(LinterError, match="could not be read"):
        await linter.lint("x", "snippet.tsx")


@requires_linter
@pytest.mark.anyio
async def test_a_crashing_helper_is_a_linter_error(tmp_path: Path) -> None:
    linter = EslintNodeLinter(fake_helper(tmp_path, 'throw new Error("boom");'))

    with pytest.raises(LinterError, match="boom"):
        await linter.lint("x", "snippet.tsx")


@requires_linter
@pytest.mark.anyio
async def test_a_hanging_helper_times_out(tmp_path: Path) -> None:
    linter = EslintNodeLinter(fake_helper(tmp_path, "setInterval(() => {}, 1000);"), timeout=0.5)

    with pytest.raises(LinterError, match="too long"):
        await linter.lint("x", "snippet.tsx")


@requires_linter
@pytest.mark.anyio
async def test_messages_do_not_leak_the_helpers_own_config() -> None:
    [message] = await real_linter().lint("const unused = 2;", "snippet.ts")

    assert message.message == "'unused' is assigned a value but never used."
