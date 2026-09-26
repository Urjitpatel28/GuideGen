# guidegen.config.json

Created by `config init`; committed by the developer. JSON schema: `../schema/config.schema.json`.
It holds **no secrets**: only environment variable names. `${VAR}` placeholders in `value`s are resolved
at runtime, and resolved values are masked in every log and JSON output.

```json
{
  "app": {
    "kind": "web | electron | wpf | winforms | winui",
    "build": "npm install",               // optional; runs before start
    "start": "npm run dev",               // web + electron
    "workingDir": ".",
    "url": "http://localhost:3210",       // web
    "executable": "src/App/bin/Debug/net9.0-windows/App.exe",   // desktop
    "args": [],
    "readyWhen": { "url": "...", "windowTitle": "...", "timeoutSec": 120 },
    "window": { "width": 1280, "height": 800 },   // desktop, logical px
    "viewport": { "width": 1440, "height": 900 }  // web
  },
  "auth": {
    "required": true,
    "usernameEnv": "GUIDEGEN_USER",
    "passwordEnv": "GUIDEGEN_PASSWORD",
    "loginSteps": [
      { "action": "goto", "value": "/login" },
      { "action": "type", "target": { "by": "label", "value": "Email" }, "value": "${GUIDEGEN_USER}" },
      { "action": "type", "target": { "by": "label", "value": "Password" }, "value": "${GUIDEGEN_PASSWORD}" },
      { "action": "click", "target": { "by": "role", "value": "button", "name": "Sign in" } }
    ]
  },
  "seed": { "command": "npm run seed", "enabled": true, "rerunBeforeTasks": true },
  "safety": {
    "allowRemoteBackends": false,
    "allowDestructive": [],               // button names or targets that are safe on this LOCAL app
    "redactPatterns": ["[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}"],
    "redactSelectors": []                 // web: CSS selectors; desktop: automation ids or names
  },
  "budget": { "maxScreens": 60, "maxTasks": 15 },
  "brand": { "productName": "", "companyName": "", "logo": "path/in/repo.svg", "primaryColor": "#1F4E79", "accentColor": "#F29F05", "version": "" },
  "graphify": { "use": "auto" },
  "brief": {
    "asked": true,                        // the phase 0 question was answered (also for "none"): never ask again
    "sources": [                          // kind: old-manual | reference-manual | outline | process
      { "kind": "old-manual", "path": "docs/Acme-Manual-2023.docx" },
      { "kind": "process", "url": "https://intranet.example.com/doc-standard", "note": "sections 2-4" }
    ],
    "notes": "Warehouse staff. Never say SKU."   // short pasted guidance; the full brief is guidegen-out/brief.md
  }
}
```

## Brief

Saved in phase 2 from the phase 0 answer (`references/brief.md`). It stores only locations, never document content.
Paths may be outside the repo; the distilled `guidegen-out/brief.md` is committed, so other machines and `--update`
do not need the originals. `config init --force` keeps the `brief` section.

## Login steps

- The first step with a target must be a field of the login form. The engine uses it to decide whether a login is needed: if that field is visible, it signs in.
- Desktop example: `{"action":"type","target":{"by":"automation_id","value":"UserNameBox"},"value":"${GUIDEGEN_USER}"}`.
- Save them with `config set auth.loginSteps '<json array>'`.

## Seed data

`seed.command` runs after the localhost check, before the app starts, and (with `rerunBeforeTasks`)
before each task capture, so that tasks which change data replay identically. Prefer seed data with fake
values: redaction cannot see text drawn inside images.

## Localhost guard

`app start` refuses (blocker `safety`) when `app.url`, or a backend setting in `appsettings.Development.json`, `.env` or
`.env.local` (connection strings, `DATABASE_URL`, `*_HOST`, `API_URL`...), points anywhere other than
localhost, 127.0.0.1, ::1 or a docker-compose service. Only set `allowRemoteBackends` if the developer
confirms the host is a disposable test backend.
