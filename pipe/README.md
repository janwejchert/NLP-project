# PIPE!

A **code-review agent** built on the [Claude Agent SDK](https://code.claude.com/docs/en/agent-sdk/python).
Point it at a file and it returns a structured review — correctness bugs, security
issues, style notes, and concrete suggestions. It runs **read-only**: it can read
and search your code but cannot edit, write, or run shell commands.

## Setup

```bash
# 1. Install dependencies (a local .venv is already created)
.venv/bin/python -m pip install -r requirements.txt

# 2. Provide your API key (get one at https://console.anthropic.com/)
export ANTHROPIC_API_KEY=sk-ant-...
# or: cp .env.example .env  and fill it in
```

## Run

```bash
.venv/bin/python main.py                  # reviews the bundled sample_code.py
.venv/bin/python main.py path/to/file.py  # review a specific file
.venv/bin/python main.py "review all .py files in this folder"
```

## How it works

`main.py` calls the SDK's `query()` with a `ClaudeAgentOptions` config:

- **`system_prompt`** — the reviewer persona and output format.
- **`allowed_tools=["Read", "Glob", "Grep"]`** — read-only; the agent literally
  cannot modify files because no Edit/Write/Bash tools are granted.
- **`permission_mode="acceptEdits"`** — auto-approves the allowed tools so it runs
  unattended.
- **`cwd`** — scopes the agent to this project directory.

The agent streams its review to the terminal, then prints a final summary with
turn count, duration, and cost.

## Customize

- **Change what it looks for** → edit `SYSTEM_PROMPT` in `main.py`.
- **Let it fix issues too** → add `"Edit"` to `allowed_tools` (no longer read-only).
- **Add a specialized sub-reviewer** → pass `agents={...}` (`AgentDefinition`) and
  include `"Agent"` in `allowed_tools`.
- **Connect external tools** → use the `mcp_servers` option (MCP).

Docs: https://code.claude.com/docs/en/agent-sdk/python
