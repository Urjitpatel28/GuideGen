# Engine CLI reference

Run it with `uv run --project <skill>/engine guidegen <command> [--json] [--out <path>] [--repo <path>]`.
Global flags can go anywhere. Exit codes: `0` ok, `1` error (`{"ok": false, "error": ...}`), `2` hard
blocker (`{"ok": false, "blocker", "message", "tried", "question", "saveTo"}`).

| Command | What it does | Key JSON fields |
|---|---|---|
| `doctor [--no-install]` | Checks Python, uv, a Chromium browser (installs Playwright's Chromium or falls back to installed Edge/Chrome), OS, desktop driver, DPI | `checks[{name,status,detail}]` |
| `detect [repo]` | Ranks candidate apps; writes `.work/detect.json` | `candidates[{rank,kind,framework,build,start,url,executable,evidence}]`, `seedCandidates`, `testEvidence`, `authHints`, `graphify` |
| `config init [--candidate N] [--force]` | Creates `guidegen.config.json` from detection + brand detection | `app`, `seed`, `brand` |
| `config set <dotted.key> <value>` | Sets one value (JSON or plain string) and validates it | |
| `config show` | Prints the validated config | |
| `validate` | Validates the config and manual.yaml with field-level errors | `problems[]` |
| `app start [--no-build]` | Localhost guard, build, seed, start, wait until ready (reuses a server that is already running) | `url` / `pid` / `cdpPort` |
| `app stop` / `app status` | Stops the whole process tree / reports state | |
| `session start` / `stop` / `status` | Driver daemon on 127.0.0.1 with a random token; starts the app if needed | `port`, `kind` |
| `tree [--depth N]` | Accessibility tree of the current view, trimmed. Web: aria snapshot plus `stable targets` (testids). Desktop: UIA tree with `automation_id`, `(no-uia)` and `(password)` flags | `view`, `tree` |
| `act '<action-json>'` | Performs one action. The destructive guard applies | `ok`, `view`, or `refused` + `reason`, or `error` |
| `shot [--file path]` | Redacted screenshot for you to look at (default `.work/shots/`) | `file`, `redactions` |
| `login [--force]` | Runs `auth.loginSteps` | |
| `reset` | Back to the start state, signed in (web: home page; desktop: restarts the app) | |
| `brief extract <file-or-url>` | Reads an old manual, reference manual, outline or process document (.docx, .pdf, .md, .txt, .html, or an http(s) URL). Works before a config exists. Writes redacted text to `.work/brief/` | `format`, `file`, `outline[{level,title,page?}]`, `words`, `redactions`, `hint?` |
| `manual init [--title]` | Creates manual.yaml | |
| `manual merge <file or ->` | Upserts screens/tasks/troubleshooting by id and deep-merges the rest. Keeps comments; never changes `override`, `exclude` or `locked` | `added`, `updated` |
| `manual remove <collection> <id> [--force]` | Deletes one item (prefer `exclude: true`). Items with override/exclude/locked are refused unless `--force` | |
| `manual show [--ids]` | Validated manual, or just ids and statuses | |
| `capture [--only id]... [--max-screens N] [--max-tasks N]` | Replays screens' `navigate` and tasks' `steps`; writes `screens/`, `capture-log.json`, statuses, `sourceHash` | `screensCaptured`, `tasks{id:status}`, `refused`, `redactions` |
| `changed` | Screens whose `source` changed since capture, plus tasks that use them | `screens[]`, `tasks[]`, `only[]` |
| `brand detect [repo] [--write]` | Logo, product/company, version, colors (of `repo`, default the current repo) | `brand`, `evidence` |
| `render [--format docx,html] [--html-single-file]` | Builds `manual.docx` and `manual-html/` (or a single `manual.html`) | `outputs`, `notes` |
| `report` | Writes `run-report.md` | `screens{}`, `tasks{}`, `redactions`, `refused`, `brief{sources,tasksFromBrief,gaps}`, `topIssues` |

Write patch files for `manual merge` inside the repo, for example `guidegen-out/.work/patch.yaml`, or pipe them on stdin with `-`.
