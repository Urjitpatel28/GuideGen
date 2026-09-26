# GuideGen - Product Requirements Document

## Problem & Vision
Developers who sell software (web apps and Windows desktop apps) rarely have an up-to-date end-user manual. Writing one by hand means clicking through every screen, taking and cropping screenshots, and writing steps, and it goes stale with every release. GuideGen is an open-source (MIT) agent skill: a developer types `/guidegen` inside Claude Code, Codex, Cursor or another agent, and the agent reads the code, runs the app, explores it, captures screenshots and produces a branded end-user manual in Word (.docx) and HTML. It follows the packaging model of `latent-spaces/brag`: the skill owns understanding (what the manual should cover), and a bundled Python engine owns mechanics (driving the app, capturing, rendering).

## Target Users
- **Primary:** solo developers and small teams shipping commercial web apps or Windows desktop apps (WPF, WinForms, WinUI, Electron) who need a manual for their customers.
- **Secondary:** consultants delivering custom software to clients who expect documentation.
- **Readers of the output:** the developer's end users, who are non-technical.

## Goals
- One command produces a complete manual (Word + HTML) with no approval stops on a typical app. The only up-front
  question is a one-time "do you already have a manual, outline or doc standard?", answered once per repo.
- First run on a sample app takes under 30 minutes of wall-clock time and zero hand-written config.
- Screen reference covers 100% of screens that are reachable in the running app.
- The How-To section contains 8-15 tasks, each backed by recorded evidence from the code.
- No passwords, tokens or email addresses are visible in any screenshot of the bundled example apps.
- Re-running after a code change (`--update`) keeps all developer edits and only re-captures changed screens.
- Installs into Claude Code, Codex, Cursor and opencode using the same methods as brag.

## Non-Goals (v1)
- macOS or Linux desktop apps, mobile apps, CLI tools, APIs without a UI.
- Custom Word templates (.dotx) or custom CSS; only logo + brand colors.
- Multiple languages / translation.
- PDF output, video walkthroughs.
- Approval checkpoints before capture.
- Round-trip editing of the generated .docx (edits go into `guidegen-out/manual.yaml`).
- A hosted service, accounts, licensing or telemetry.
- Graphify as a requirement (it is an optional input only).
- Driving controls with no accessibility tree (custom-drawn canvases, OpenGL/CAD viewports); these are screenshotted as a whole window only.

## Core Features (v1)
1. **Install anywhere** - Claude Code plugin marketplace, `npx skills add`, or copying the folder; symlinked discovery paths for Claude Code, Codex and opencode.
2. **Project detection** - identifies app type (web framework or Windows desktop framework), build/start commands, URL or executable.
3. **App startup** - builds and starts the app, waits for it to be ready, logs in, runs seed data if the repo provides it. Stops only on hard blockers and saves the answers to `guidegen-out/guidegen.config.json`.
4. **Surface inventory** - lists every user-facing screen (routes, windows, dialogs, forms) from the code; optionally enriched by an existing `graphify-out/`.
5. **Task discovery** - proposes 8-15 how-to tasks ranked by evidence (E2E/UI tests, form dependencies, README/onboarding, graphify clusters).
6. **Exploration & capture** - drives the app (Playwright for web and Electron, pywinauto UIA for WPF/WinForms/WinUI), confirms each screen is reachable, captures annotated screenshots.
7. **Safety guards** - redacts secrets in screenshots, refuses destructive actions and non-local backends unless allowed in config.
8. **Manual writing** - Getting Started, How-To Tasks, Screen Reference, Troubleshooting; written in plain language for end users; cross-linked.
9. **Branding** - auto-detects logo, product name, company and colors; overridable in config.
10. **Rendering** - `guidegen-out/manual.docx` and `guidegen-out/manual-html/index.html`. Everything GuideGen creates (config, manual.yaml, screenshots, outputs, report) lives in one `guidegen-out/` folder in the project root, with its own `.gitignore`; `--out <path>` changes the location.
11. **Update mode** - `/guidegen --update` re-uses `manual.yaml`, keeps edits, re-captures only screens whose source changed.
12. **Run report** - lists what was captured, skipped (with reason), cut by budget, and redacted.

## User Stories
- As a developer, I want to install GuideGen with one command in my agent, so that I can use it in any project.
- As a developer, I want to type `/guidegen` and get a finished manual, so that I don't spend days writing one.
- As a developer, I want GuideGen to ask me only when it truly cannot continue (e.g. login), and remember my answer, so that later runs need no input.
- As a developer with an existing manual, outline or documentation standard, I want GuideGen to ask for it once and follow its structure, terms and tone, so that the new manual matches what my customers already know.
- As a developer, I want every reachable screen documented, so that customers can look up any window they see.
- As a developer, I want step-by-step task guides with a screenshot per step, so that customers can complete real workflows.
- As a developer, I want my logo and colors on the manual, so that it looks like part of my product.
- As a developer, I want secrets hidden in screenshots and destructive actions blocked, so that running GuideGen is safe.
- As a developer, I want to fix titles, text, and remove screens by editing one file, so that my changes survive regeneration.
- As a developer, I want to re-run after a release and only update what changed, so that the manual stays current cheaply.
- As a developer, I want a report of what was skipped and why, so that I know exactly how complete the manual is.
- As an end user, I want a searchable HTML manual and a printable Word manual, so that I can learn the product my way.

## Success Metrics
- On the three bundled example apps (Next.js, WPF, WinForms): 100% of reachable screens captured, >= 8 tasks generated, 0 secrets visible, first run with no hand-written config.
- `--update` run after changing one screen re-captures only that screen and preserves all overrides.
- Community signal after launch: GitHub stars, installs via skills.sh, and at least one community-contributed framework recipe within 3 months.

## Future Considerations
- Custom .dotx templates and CSS themes; PDF export.
- Multi-language manuals.
- FlaUI (.NET) helper as an alternative desktop driver.
- macOS desktop apps; mobile apps via emulators.
- Short GIF/video clips per task.
- CI mode (regenerate manual on each release tag).
