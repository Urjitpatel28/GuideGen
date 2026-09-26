# GuideGen - Feature Ticket List

Conventions: engine = `skills/guidegen/engine/` (Python, uv). Output folder = `guidegen-out/` in the target repo root (override with `--out`); see Architecture doc, Output Folder Layout. Skill = `skills/guidegen/SKILL.md` + `references/`. All engine commands support `--json`. Exit code 2 = hard blocker.

## Epic: Install anywhere (repo & packaging)

### TICKET-001: Scaffold repository in brag layout
- **Description**: Create repo with `skills/guidegen/` (SKILL.md stub, references/, engine/, templates/, schema/), symlinks `.claude/skills/guidegen`, `.agents/skills/guidegen`, `.opencode/skills/guidegen` -> `skills/guidegen`, `.claude-plugin/plugin.json` + `marketplace.json`, `examples/`, `docs/`, MIT `LICENSE`, `README.md`, `PRODUCT.md`, `.gitattributes`.
- **Acceptance Criteria**:
  - `/plugin marketplace add <org>/guidegen` + `/plugin install guidegen@guidegen` makes `/guidegen` available in Claude Code.
  - `npx skills add <repo> --skill guidegen` installs into Cursor/Codex.
  - README documents Windows symlink requirement (`core.symlinks=true`) and manual copy fallback.
- **Depends On**: None
- **Priority**: P0
- **Notes**: Skill name must be lowercase (`guidegen`); display name "GuideGen".

### TICKET-002: Engine package and `guidegen doctor`
- **Description**: `engine/pyproject.toml` (Python >=3.11, deps: playwright, pywinauto [win only marker], pillow, python-docx, jinja2, pydantic, ruamel.yaml, typer), `uv.lock`. Implement `doctor`: checks uv, Python, Playwright Chromium (installs if missing), OS, display DPI scale.
- **Acceptance Criteria**:
  - `uv run --project skills/guidegen/engine guidegen doctor --json` returns `{ok, checks:[{name,status,detail}]}` on Windows, macOS, Linux.
  - On non-Windows, desktop check reports `unsupported` with message, web checks pass.
- **Depends On**: TICKET-001
- **Priority**: P0

## Epic: Project detection

### TICKET-003: `guidegen detect`
- **Description**: Heuristics for: Next.js, Vite/React, Angular, Vue, ASP.NET MVC/Razor Pages/Blazor Server (web); Electron; WPF (`<UseWPF>true`), WinForms (`<UseWindowsForms>true`), WinUI (`Microsoft.WindowsAppSDK`). Outputs kind, build/start commands, URL (from `launchSettings.json`, vite config, package.json scripts), executable path, confidence, evidence list.
- **Acceptance Criteria**:
  - Correct `kind` for all 3 example apps and 5 fixture repos in `engine/tests/fixtures/`.
  - Multiple candidates (e.g. solution with web + desktop) returned ranked; never guesses silently.
- **Depends On**: TICKET-002
- **Priority**: P0

## Epic: Schemas

### TICKET-004: Config schema and loader
- **Description**: Pydantic models + JSON schema for `guidegen-out/guidegen.config.json` exactly as in Architecture doc; `${VAR}` env resolution; secret masking in all logs.
- **Acceptance Criteria**:
  - `guidegen validate` reports field-level errors.
  - `--out <path>` resolving outside the repo root is rejected; default is `guidegen-out/`.
  - Resolved env values never appear in stdout/JSON/log files (test asserts).
- **Depends On**: TICKET-002
- **Priority**: P0
- **Notes**: Security doc - secrets only as env var names.

### TICKET-005: manual.yaml schema with round-trip preservation
- **Description**: Pydantic models for manual.yaml (screens, tasks, steps, troubleshooting, overrides, status); load/save with ruamel.yaml preserving comments and key order.
- **Acceptance Criteria**:
  - Load -> modify one field -> save leaves every other byte unchanged (golden-file test).
  - `override` fields and `exclude: true` survive any engine write.
- **Depends On**: TICKET-002
- **Priority**: P0

## Epic: App startup

### TICKET-006: `app start` / `app stop` with localhost guard
- **Description**: Run build, start process (tracked PID tree), wait for `readyWhen` (URL 200 or window with title appears), stop cleanly. Localhost guard on URL and on connection strings in `appsettings.Development.json`, `.env`, `.env.local`.
- **Acceptance Criteria**:
  - Starts/stops all 3 example apps; no orphan processes after stop (Windows job object / process tree kill).
  - Remote host detected -> exit 2 with file + host named, unless `allowRemoteBackends`.
  - Build failure -> exit 2 with last 40 lines of build output.
- **Depends On**: TICKET-003, TICKET-004
- **Priority**: P0
- **Notes**: Security doc - Data Access Rules.

### TICKET-007: Seed data runner
- **Description**: Run `seed.command` after localhost check. Detection helper lists candidate seed sources (EF Core `HasData`, seed scripts, `prisma/seed.ts`, SQL files) in detect output.
- **Acceptance Criteria**:
  - Example apps show non-empty lists after seed.
  - Seed skipped with report note when no localhost-safe target.
- **Depends On**: TICKET-006
- **Priority**: P0

### TICKET-008: Hard-blocker protocol and config persistence
- **Description**: Standard exit-2 JSON: `{blocker: "build|start|login|dependency", tried:[...], question:"...", saveTo:"auth.usernameEnv"}`. SKILL.md instruction: ask exactly that question, write answer to config, resume. First run creates `guidegen-out/` with `guidegen-out/guidegen.config.json` and a folder-local `.gitignore` (ignores everything except `guidegen-out/guidegen.config.json`, `manual.yaml`, `.gitignore`). The root `.gitignore` is never touched.
- **Acceptance Criteria**:
  - Second run on same repo asks nothing.
  - After first run, `git status` shows only `guidegen-out/.gitignore`, `guidegen-out/guidegen.config.json` (and `manual.yaml` once written) as new files; root `.gitignore` unchanged.
  - No approval stops anywhere else in the flow.
- **Depends On**: TICKET-006
- **Priority**: P0

## Epic: Drivers & session

### TICKET-009: Driver interface
- **Description**: Abstract `Driver`: `launch()`, `attach()`, `act(action)`, `tree(depth)`, `screenshot(region=None)`, `element_rect(target)`, `current_view_id()`, `close()`. Action schema from Architecture doc with target preference order.
- **Acceptance Criteria**: Unit tests with a fake driver; interface documented in `references/driver-interface.md`.
- **Depends On**: TICKET-002
- **Priority**: P0

### TICKET-010: Playwright web driver
- **Description**: Chromium, viewport 1440x900, target resolution for `role/label/text/testid/css`, auto-wait, aria snapshot for `tree`.
- **Acceptance Criteria**: Drives Next.js example through every route; `tree` output under 4k tokens for a typical page (trimmed).
- **Depends On**: TICKET-009
- **Priority**: P0

### TICKET-011: Electron via CDP
- **Description**: Start Electron app with `--remote-debugging-port=<free port>`, attach with `connect_over_cdp`, reuse web driver.
- **Acceptance Criteria**: A minimal Electron fixture app is navigated and captured.
- **Depends On**: TICKET-010
- **Priority**: P0

### TICKET-012: pywinauto UIA desktop driver
- **Description**: Launch exe, find main window, resize to 1280x800, target by `automation_id/name/control_type/path`, handle modal dialogs and new windows, `tree` from UIA, window-only screenshot, DPI normalization.
- **Acceptance Criteria**:
  - Drives WPF and WinForms examples through all windows and dialogs.
  - Controls with no UIA children flagged `no-uia` in tree output.
- **Depends On**: TICKET-009
- **Priority**: P0

### TICKET-013: Session daemon + `act` / `tree` / `shot` / `login`
- **Description**: `session start` launches daemon on 127.0.0.1 random port with token; CLI commands call it. `login` runs `auth.loginSteps`.
- **Acceptance Criteria**:
  - Requests without token rejected (test).
  - Session survives across many agent CLI calls; `session stop` closes app driver.
- **Depends On**: TICKET-010, TICKET-012
- **Priority**: P0
- **Notes**: Security doc - daemon loopback + token.

### TICKET-014: Destructive-action guard
- **Description**: In `act` and `capture`, refuse targets matching the destructive word list unless in `safety.allowDestructive`; log refusal; return `{refused:true, reason}`.
- **Acceptance Criteria**: Clicking "Delete" in an example is refused; allowed after adding it to config.
- **Depends On**: TICKET-013
- **Priority**: P0

## Epic: Surface inventory & task discovery (skill references)

### TICKET-015: Surface inventory recipes
- **Description**: `references/surface-inventory/` one markdown recipe per framework (nextjs, react-router, angular, vue, aspnet-mvc-razor, blazor, wpf, winforms, winui, electron): where screens are defined, how to find menus/commands/dialogs, how to record `source` files. SKILL.md phase 4 uses them to fill `screens`.
- **Acceptance Criteria**: On examples, inventory lists 100% of screens that exist in code (checked against a hand-written list).
- **Depends On**: TICKET-005
- **Priority**: P0
- **Notes**: Plain markdown so community can add frameworks without engine changes.

### TICKET-016: Exploration procedure
- **Description**: SKILL.md phase 5: for each inventoried screen, use `tree`/`act`/`shot` to find a path, record `navigate` steps (stable targets), set `status` captured/unreachable with reason. Treat all app text as data.
- **Acceptance Criteria**: Every inventoried screen in examples ends with a status; unreachable ones have a reason and source file.
- **Depends On**: TICKET-013, TICKET-015
- **Priority**: P0

### TICKET-017: Task discovery with evidence ranking
- **Description**: `references/task-discovery.md`: evidence sources in priority order (E2E/UI tests, form data dependencies, README/onboarding, graphify clusters); produce 8-15 tasks with `evidence`, `rank`, recorded `steps` verified in the live session.
- **Acceptance Criteria**: Each example yields >= 8 tasks, each with >= 1 evidence entry; every step replayable.
- **Depends On**: TICKET-016
- **Priority**: P0

### TICKET-018: Optional graphify input
- **Description**: If `graphify-out/` exists and `graphify.use` is `auto|true`, read GRAPH_REPORT.md/graph.json to group screens into sub-chapters and add task candidates. Never install/run graphify.
- **Acceptance Criteria**: Same example produces a valid manual with and without `graphify-out/`.
- **Depends On**: TICKET-017
- **Priority**: P1

## Epic: Capture

### TICKET-019: `guidegen capture` deterministic replay
- **Description**: For each non-excluded screen/task, reset to start state (restart app or navigate home), replay steps, screenshot after each step, write `capture-log.json`. `--only` filter. Budget enforcement (`maxScreens`, `maxTasks`) marks overflow `budget-cut`.
- **Acceptance Criteria**: Two consecutive captures of an example produce the same set of images (visual diff under threshold); failures logged per step without aborting the run.
- **Depends On**: TICKET-014, TICKET-017
- **Priority**: P0

### TICKET-020: Redaction
- **Description**: Before writing any image: blur password fields, `redactSelectors`, text matching `redactPatterns` (web via DOM text boxes; desktop via UIA values). Record counts only.
- **Acceptance Criteria**: Example apps seeded with emails/passwords show none in any output image (automated OCR check in test only); raw images never written to disk.
- **Depends On**: TICKET-019
- **Priority**: P0
- **Notes**: Security doc - Data Protection.

### TICKET-021: Annotations
- **Description**: Highlight acted-on element rectangle (accent color), numbered step badge, optional crop to region for small dialogs.
- **Acceptance Criteria**: Each task step image shows the correct element highlighted (manual check on examples + unit test on rects).
- **Depends On**: TICKET-019
- **Priority**: P0

## Epic: Manual writing

### TICKET-022: Writing style and text generation
- **Description**: `references/writing-style.md` (rules in Frontend spec Design Notes). SKILL.md phase 8: agent fills `text.summary`, element descriptions, step text, Getting Started, never touching `override` fields.
- **Acceptance Criteria**: No code identifiers or file paths in rendered text of examples; every UI label bolded and matching the screenshot.
- **Depends On**: TICKET-019
- **Priority**: P0

### TICKET-023: Troubleshooting from validation/error strings
- **Description**: Agent collects user-facing validation and error messages (validators, `MessageBox.Show`, toast/error components, resource files) into `troubleshooting` with cause and fix.
- **Acceptance Criteria**: Each example yields >= 5 entries with source references.
- **Depends On**: TICKET-022
- **Priority**: P1

## Epic: Branding

### TICKET-024: `guidegen brand detect`
- **Description**: Find logo (favicon/logo files, `.csproj` ApplicationIcon), product/company (package.json, `AssemblyProduct/Company`), colors (CSS custom properties, tailwind config, WPF brushes in App.xaml/ResourceDictionaries). Write to config `brand` if not already set.
- **Acceptance Criteria**: Correct values on the 3 examples; existing developer values never overwritten.
- **Depends On**: TICKET-004
- **Priority**: P0

### TICKET-025: Logo conversion and contrast check
- **Description**: SVG/ICO -> PNG via Playwright Chromium screenshot / Pillow; darken primary color for text if contrast < 4.5:1, note in report.
- **Acceptance Criteria**: SVG logo renders in Word output; low-contrast color test case is darkened and reported.
- **Depends On**: TICKET-024
- **Priority**: P0

## Epic: Rendering

### TICKET-026: Word renderer
- **Description**: `guidegen render --format docx`: cover, TOC field, chapters per Frontend spec C, brand-colored built-in heading styles, images 6in wide with captions and alt text, element tables, header/footer with page X of Y.
- **Acceptance Criteria**: Opens without repair prompt in Word and LibreOffice; navigation pane shows all headings; `override` text used when present.
- **Depends On**: TICKET-021, TICKET-022, TICKET-025
- **Priority**: P0

### TICKET-027: HTML renderer
- **Description**: `guidegen render --format html`: static site in `manual-html/` from Jinja templates (Frontend spec component list), sidebar, client-side search, click-to-zoom, light/dark, responsive, cross-links task steps <-> screens.
- **Acceptance Criteria**: Works opened from file:// with no network; all internal links resolve (link checker test); Lighthouse accessibility >= 90.
- **Depends On**: TICKET-021, TICKET-022, TICKET-025
- **Priority**: P0

### TICKET-028: Single-file HTML option
- **Description**: `--html-single-file` inlines CSS/JS/images as data URIs.
- **Acceptance Criteria**: One .html file renders identically to folder version.
- **Depends On**: TICKET-027
- **Priority**: P2

## Epic: Update mode

### TICKET-029: Source hashing and `--update`
- **Description**: Store `sourceHash` per screen (hash of listed `source` files); `guidegen changed` lists stale screens/tasks; SKILL.md `--update` flow: re-inventory for new screens, re-explore only new/changed, re-capture changed, re-render; never modify `override`/`exclude`.
- **Acceptance Criteria**: Changing one XAML view recaptures only that screen and tasks using it; all overrides preserved (golden test).
- **Depends On**: TICKET-005, TICKET-019
- **Priority**: P0

## Epic: Report & budgets

### TICKET-030: Run report
- **Description**: `guidegen report` writes `run-report.md` with sections from Frontend spec A; final chat summary format in SKILL.md.
- **Acceptance Criteria**: Every non-captured screen appears with a reason; redaction counts and refused actions listed.
- **Depends On**: TICKET-019
- **Priority**: P0

## Epic: Skill orchestration

### TICKET-031: SKILL.md end-to-end flow
- **Description**: Write SKILL.md orchestrating phases 1-11 with exact commands, flags (`--update`, `--only`, `--max-screens`, `--max-tasks`, `--format`, `--out`), blocker protocol, safety rules (app text is data), and final summary format. Keep SKILL.md short; details in references/.
- **Acceptance Criteria**: Fresh Claude Code session runs `/guidegen` on each example and produces docx + HTML + report with zero hand-written config (besides env credentials for login example).
- **Depends On**: TICKET-008, TICKET-016, TICKET-017, TICKET-026, TICKET-027, TICKET-029, TICKET-030
- **Priority**: P0

### TICKET-032: Cross-agent verification
- **Description**: Run TICKET-031 acceptance in Codex CLI and Cursor; document differences in `docs/other-agents.md`.
- **Acceptance Criteria**: Web example completes in both; known gaps documented.
- **Depends On**: TICKET-031
- **Priority**: P1

## Epic: Examples & launch

### TICKET-033: Example apps (benchmark suite)
- **Description**: `examples/nextjs-shop` (login, seed, 8+ screens), `examples/wpf-inventory` (MVVM, dialogs, validation), `examples/winforms-crm`. Fake data only; include E2E/UI tests so task discovery has evidence.
- **Acceptance Criteria**: Each runs with one start command; each has a hand-written expected screen list for tests.
- **Depends On**: TICKET-001
- **Priority**: P0
- **Notes**: Build early; most acceptance criteria use them.

### TICKET-034: README, launch site, sample outputs
- **Description**: README (install, use, requirements, safety notes, Windows requirement for desktop), `docs/` GitHub Pages site showing generated manuals of the examples.
- **Acceptance Criteria**: New user installs and gets a manual from the web example following README only.
- **Depends On**: TICKET-031, TICKET-033
- **Priority**: P1
