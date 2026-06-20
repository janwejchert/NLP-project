"""PIPE! — a code-review agent built on the Claude Agent SDK.

Point it at a file (or let it scan the project) and it produces a structured
code review: correctness bugs, security issues, style/readability notes, and
concrete suggestions. It runs in READ-ONLY mode — it can read and search the
code but cannot edit, write, or run shell commands.

Usage:
    python main.py                      # review sample_code.py (the default target)
    python main.py path/to/file.py      # review a specific file
    python main.py "the whole project"  # free-form instruction also works

Requires the ANTHROPIC_API_KEY environment variable (see .env.example).
"""

import asyncio
import os
import sys
from pathlib import Path

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    query,
)

# --- The reviewer's persona / instructions -------------------------------------
# The system prompt shapes *how* the agent reviews. Tweak this to change its
# focus, tone, or output format.
SYSTEM_PROMPT = """You are PIPE!, a meticulous senior code reviewer.

When reviewing code:
1. Read the target file(s) first using the Read/Glob/Grep tools.
2. Report findings grouped under these headings, most important first:
   - 🐞 Correctness & bugs
   - 🔒 Security
   - 🧹 Readability & style
   - 💡 Suggestions
3. For each finding cite the file and line, explain *why* it matters, and show
   a concrete fix or improved snippet.
4. If a category has no issues, say so in one line — don't invent problems.
5. End with a one-sentence overall verdict.

Be specific and actionable. You are read-only: never attempt to edit files."""


def build_options(project_dir: Path) -> ClaudeAgentOptions:
    """Configure the agent: read-only tools, the reviewer persona, and the
    working directory the agent is allowed to operate in."""
    return ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        # Auto-approve these read-only tools so the agent runs unattended.
        allowed_tools=["Read", "Glob", "Grep"],
        # Hard block all mutating tools. allowed_tools only pre-approves; this
        # disallow list is what actually guarantees the agent stays read-only.
        disallowed_tools=["Edit", "MultiEdit", "Write", "Bash", "NotebookEdit"],
        # Auto-allow the pre-approved tools without interactive prompts.
        permission_mode="acceptEdits",
        # A code review is a bounded task; cap turns to keep cost predictable.
        max_turns=20,
        # Scope the agent to this project directory.
        cwd=str(project_dir),
    )


async def review(target: str, project_dir: Path) -> int:
    """Run a single review pass and stream the output. Returns a process exit code."""
    prompt = f"Review the following and give me a full code review: {target}"
    options = build_options(project_dir)

    had_error = False
    # query() opens a fresh session and yields messages as the agent works.
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            # An assistant turn is a list of content blocks; print the text ones
            # as they stream in.
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(block.text, end="", flush=True)
        elif isinstance(message, ResultMessage):
            # The final message carries status, timing, and cost.
            print("\n" + "─" * 60)
            if message.is_error:
                had_error = True
                print(f"⚠️  Finished with error: {message.subtype}")
            else:
                print("✅ Review complete.")
            print(f"   Turns: {message.num_turns}  |  Time: {message.duration_ms} ms", end="")
            if message.total_cost_usd is not None:
                print(f"  |  Cost: ${message.total_cost_usd:.4f}")
            else:
                print()

    return 1 if had_error else 0


def load_env_file(path: Path) -> None:
    """Minimal .env loader (no external dependency). Reads simple KEY=VALUE
    lines and sets them in the environment if not already present."""
    if not path.is_file():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip("'\"")
        os.environ.setdefault(key, value)


async def main() -> int:
    project_dir = Path(__file__).resolve().parent
    # Pick up ANTHROPIC_API_KEY from a local .env file if present (shell
    # environment variables still take precedence).
    load_env_file(project_dir / ".env")

    # Default to reviewing the bundled sample file if no argument is given.
    target = " ".join(sys.argv[1:]).strip() or "sample_code.py"

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print(
            "ERROR: ANTHROPIC_API_KEY is not set.\n"
            "Set it first, e.g.:  export ANTHROPIC_API_KEY=sk-ant-...\n"
            "Get a key at https://console.anthropic.com/",
            file=sys.stderr,
        )
        return 2

    print(f"🔍 PIPE! reviewing: {target}\n")
    try:
        return await review(target, project_dir)
    except Exception as exc:  # noqa: BLE001 - surface any SDK/runtime error cleanly
        print(f"\nUnexpected error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
