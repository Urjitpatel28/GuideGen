# GuideGen - product summary

**What**: an agent skill that turns a software project into an end-user manual (Word + HTML) with one command.

**Who**: solo developers, small teams and consultants shipping web apps or Windows desktop apps (WPF,
WinForms, WinUI, Electron) whose customers need a manual.

**Why**: hand-written manuals take days (click through every screen, crop screenshots, write steps) and go
stale with every release. GuideGen does the first draft in minutes, and `--update` keeps it current by
re-capturing only what changed while preserving every edit.

**How**: the skill owns understanding (which screens exist, which tasks matter, the words). The bundled engine
owns mechanics (running and driving the app, deterministic replay, redaction, annotation, rendering). This is the same
split as [latent-spaces/brag](https://github.com/latent-spaces/brag).

**v1 scope**: web + Windows desktop; Word + HTML; logo and brand colors; update mode; run report.
**Not in v1**: macOS/Linux desktop, mobile, PDF, custom templates, translations, hosted service, telemetry.

**Success**: on the bundled examples, 100% of reachable screens captured, 8 or more tasks, no secrets visible, and no
hand-written config. `--update` after changing one screen re-captures only that screen and keeps all overrides.

Specs: `docs/01-prd.md` (PRD), `docs/02-technical-architecture.md`, `docs/03-security-and-access.md`,
`docs/04-frontend-spec.md`, `docs/05-feature-tickets.md`.
