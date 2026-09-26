# GuideGen in other agents

GuideGen is a plain Agent Skill (`SKILL.md` + `references/` + an engine run through `uv`), so any agent that
can read skills and run shell commands can use it.

| Agent | Install | Invoke | Notes |
|---|---|---|---|
| Claude Code | plugin marketplace, or `.claude/skills/guidegen` | `/guidegen` | Reference agent; the examples were verified here |
| Codex CLI | `npx skills add ... --skill guidegen`, or `.agents/skills/guidegen` | "use the guidegen skill" or `$guidegen` | Allow `uv` in the sandbox. The engine binds 127.0.0.1 only |
| Cursor | `npx skills add ... --skill guidegen` | "/guidegen" in Agent mode | Run in Agent mode (tools enabled) |
| opencode | `.opencode/skills/guidegen` | "use guidegen" | |

## Phase 0 question

Every agent asks the one-time brief question the same way (see `skills/guidegen/references/brief.md`). Agents that
run without a person watching should be started with `--brief <file|url>` or `--no-brief`, so the run does not wait
for an answer. `brief extract` reads PDFs itself, so agents that cannot view PDFs still get the text.

## Known gaps

- **Network sandboxes**: the first run downloads Python packages with `uv`. `doctor` uses an installed Edge or Chrome
  when Playwright's Chromium cannot be downloaded.
- **Long-running commands**: `capture` can take several minutes (about 2-5 minutes for the examples). Agents with
  short command timeouts should run it with `--only` in batches.
- **Desktop apps** need a real interactive Windows session (UI Automation and window screenshots do not work in
  headless or service sessions).
- Cross-agent runs (TICKET-032) have not been benchmarked yet; please report results in an issue.
