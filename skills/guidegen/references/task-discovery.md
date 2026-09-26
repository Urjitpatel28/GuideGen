# Phase 6: Task discovery

Produce **8-15** how-to tasks (or up to `budget.maxTasks`). Each one is a real workflow a customer would
look up, backed by evidence from the code, ranked, and verified step by step in the live session.

## Evidence sources, strongest first

0. **The developer's brief** (`guidegen-out/brief.md`, see `brief.md`): tasks from an old manual or an outline, in
   the brief's order and with its titles. Still verified live. Items the app does not have go into `briefGaps`.
   `type: brief`, `ref: <source> §<section>`.
1. **E2E / UI tests** (`testEvidence` in detect.json: Playwright/Cypress specs, FlaUI/Appium/WinAppDriver
   tests). Each test that walks a user flow is a task candidate. Its steps map almost directly to your steps.
   `type: e2e-test` or `ui-test`.
2. **Form data dependencies**: an entity that requires another (an order needs a customer, an item needs a
   category) implies both "create X" tasks and their order. `type: form-dependency`, `ref` in words.
3. **README / onboarding / docs / empty states / "Get started" UI**. `type: readme` or `onboarding`.
4. **graphify clusters** (optional, `references/graphify.md`). `type: graphify`.
5. **Code only** (a command, menu item or button with clear user value). `type: code`, `ref: file + symbol`.

Rank brief tasks first, in the brief's order. Rank the rest by evidence strength and user value: sign-in and the core create/record flows first; settings, lookup and
"find" tasks next; destructive tasks (delete, send) last.

## Writing a task

- `title`: imperative, the user's words ("Create an order", not "OrderForm submission").
- `goal`: one sentence on the outcome.
- `steps`: one action per step, starting from the start state (signed in, home). Put the tab or menu click first when needed.
  Every step gets a `screen` so the manual cross-links to the Screen Reference.
- Fake data only in `type` values. Use `${GUIDEGEN_USER}` / `${GUIDEGEN_PASSWORD}` for credentials.
- Selects: use the option **value** (stable) rather than a label that contains changing numbers.
- **Verify** every task live: `reset`, then `act` each step and check `view` / `shot`. Fix targets until it replays.
- Destructive final steps (Send, Delete, Pay) are allowed as the **last** step. The engine refuses them and
  keeps the "before" screenshot, and your step text still explains what happens.
- Sign-in task: `beforeLogin: true`.

Budget: tasks beyond `budget.maxTasks` (by rank) are `budget-cut` and listed in the report. The 8-15 range is a default:
when the brief lists more tasks than `budget.maxTasks`, keep them all and tell the developer to raise the budget.
