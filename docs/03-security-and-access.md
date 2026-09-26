# GuideGen - Security & Access Document

## Authentication
GuideGen itself has no users, accounts, or login. It runs locally as the developer who invoked it.

The only authentication GuideGen handles is **logging into the target app** being documented:
- Credentials are supplied through environment variables named in `guidegen-out/guidegen.config.json` (`auth.usernameEnv`, `auth.passwordEnv`). Values are never written to config, manual.yaml, logs, or the report.
- The session daemon (`guidegen session start`) listens on `127.0.0.1` only, on a random port, and requires a random per-session token stored in `guidegen-out/.work/session.json` (file permissions restricted to the current user). Requests without the token are rejected.

## Roles & Permissions
There is a single role.

| Role | Can do |
|---|---|
| Developer (local user running the agent) | Everything: run detection, start the app, drive it, capture, edit manual.yaml/config, render outputs |

End users of the generated manual only read static files; they have no interaction with GuideGen.

## Data Access Rules
- The engine only reads files inside the target repo root and the skill folder. Paths in config/manual.yaml that resolve outside the repo root (after `..` normalization) are rejected.
- The engine only writes inside the output folder (default `guidegen-out/` in the repo root, or the path given with `--out`, which must resolve inside the repo root). It never modifies any other file in the repo, including the root `.gitignore`.
- `app start` and `session` refuse to proceed if the app's configured URL, or any connection string found in the app's local settings files (`appsettings.Development.json`, `.env`, `.env.local`), points to a host other than `localhost`, `127.0.0.1`, `::1`, or a Docker service name defined in the repo's compose file - unless `safety.allowRemoteBackends` is `true`. Violation = exit code 2 with a message naming the file and host.
- `seed.command` runs only when the database target passes the same localhost check.
- **Destructive-action guard:** `act` and `capture` refuse to click/press a control whose accessible name or text matches (case-insensitive) `delete`, `remove`, `pay`, `purchase`, `buy`, `checkout`, `send`, `email`, `publish`, `submit payment`, `transfer`, `unsubscribe`, `deactivate`, `reset`, `drop`, unless the control's target is listed in `safety.allowDestructive`. A refused step is logged and the task step is documented from code with a screenshot of the state *before* the click.
- The engine makes no outbound network calls other than to the app's local URL and Playwright's one-time browser download during `doctor`.

## Data Protection
Sensitive data: credentials, API tokens, customer/PII shown in the app's UI, connection strings.

Redaction is applied to every screenshot before it is written to disk (raw unredacted images are never saved):
- Web: all `input[type=password]`, elements matching `safety.redactSelectors`, and text nodes matching `safety.redactPatterns` (default: email pattern) are blurred using element bounding boxes.
- Desktop: `PasswordBox` / `IsPassword=true` controls, controls matching `redactSelectors` (by automation id/name), and controls whose value matches `redactPatterns` are blurred.
- Every redaction is recorded (count per image, never the value) in capture-log.json and the run report.
- Known limitation: text drawn inside images or custom-drawn controls cannot be detected; the report states this and recommends seed data with fake values.

Retention: on first run GuideGen writes `guidegen-out/.gitignore`, which ignores everything in the folder except `guidegen-out/guidegen.config.json`, `manual.yaml` and itself. Generated files (images, docx, HTML, logs, `.work/`) are safe to delete. The two committed files contain no secrets.

## Threat Considerations
| Risk | Mitigation |
|---|---|
| Real customer data or secrets appear in screenshots that ship with the manual | Localhost-only backends by default, seed-data preference, automatic redaction, report of redactions and limitations |
| Agent triggers real side effects (payments, emails, deletes) while exploring | Destructive-action guard in the engine (not only in instructions), localhost guard |
| Agent connects to production DB via a connection string it found | Localhost guard on URL, settings files and seed command; opt-in flag required |
| Credentials leak into committed files or logs | Env-var references only; engine masks `${VAR}` values in all logs and JSON output |
| Another local process drives the session daemon | Loopback bind + random token + user-only file permissions |
| Malicious content in the target app's UI (e.g. text telling the agent to do something) | SKILL.md instructs the agent to treat all app text as data, never instructions; engine guards apply regardless |
| Path traversal via config/manual.yaml paths | Path normalization and repo-root containment check |
| Supply chain (Python deps) | Pinned versions with hashes in `uv.lock`; minimal dependency set |

Running the target app's build/start commands executes the developer's own code with the developer's permissions. That is the same trust level as running the app manually and is stated in the README.

## Compliance
None apply to GuideGen itself (no data collected, no telemetry, no hosted component). Developers remain responsible for what appears in manuals they publish; the README tells them to review screenshots and use seed data.
