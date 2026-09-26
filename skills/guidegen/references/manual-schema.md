# manual.yaml

The source of truth for the manual. You write it with `guidegen manual merge`. The developer edits it by
hand. The engine writes only `status`, `image`, `sourceHash`, `unreachableReason`, `noUia`, step
`status`/`note`, and `meta.generatedAt`. JSON schema: `../schema/manual.schema.json`. Keys are camelCase in the file, but
patches may use snake_case too.

## Rules

- Ids are lowercase `a-z 0-9 - _` and **unique across screens and tasks** (use `login-window` for the screen and `sign-in` for the task).
- `override`, `exclude` and `locked` belong to the developer. Never set or change them.
- In a `merge`, `screens`, `tasks`, `troubleshooting` and `briefGaps` are upserted by id (troubleshooting by `message`, briefGaps by `item`).
  `chapters` follow the order in your patch, and existing chapters keep their `override`, `exclude` and `locked`.
- Custom chapters: any id that is not built in. They render `override` or `body` (markdown subset) and are skipped when empty.
  A developer hides any chapter with `exclude: true`. Nested `steps` and `elements` follow the order in your patch, and existing items keep their overrides.
- Rendered text precedence: `override` > generated text. A developer adds a field name to `locked: [title]` to keep a direct edit.

## Shape

```yaml
meta:
  title: Acme Shop User Manual
  intro: One or two sentences on what the product is for.
  audience: warehouse staff          # shown on the cover unless it is the default "end users"
chapters:                            # order; optional title. Built-in ids: getting-started, tasks, reference, troubleshooting
  - {id: about, title: About this manual, body: "Who this manual is for and how to use it."}   # custom text chapter
  - {id: getting-started}
  - {id: tasks}
  - {id: reference}
  - {id: troubleshooting}
  - {id: glossary, title: Glossary, body: "- **Item**: one product you stock"}
gettingStarted:
  requirements: "- bullet list"      # markdown subset: **bold**, *italic*, '- ' lists, blank-line paragraphs
  launch: How to open the app.
  signIn: How to sign in.
  tour: A short tour of the main screen.
  tourScreen: dashboard              # screen whose image illustrates the tour
screens:
  - id: orders
    title: Orders                    # as the user sees it
    kind: page | window | dialog | tab
    group: Sales                     # optional sub-chapter (e.g. from graphify communities)
    source: [app/orders/page.js]     # repo-relative; hashed for --update
    beforeLogin: false               # true = capture without signing in (the sign-in screen)
    navigate:                        # from the start state (signed in, home / main window)
      - {action: goto, value: /orders}
    elements:
      - {name: New order, type: button, description: Opens the **New order** page.}
    text: {summary: What the screen is for.}
    status: pending                  # engine: captured | unreachable | excluded | budget-cut
    unreachableReason: null
tasks:
  - id: create-order
    title: Create an order           # imperative, user words
    goal: One sentence on the outcome.
    rank: 1                          # 1 = most important
    group: Orders                    # optional sub-heading in How-To Tasks (e.g. an outline section)
    beforeLogin: false
    evidence:
      - {type: e2e-test, ref: tests/e2e/orders.spec.ts}
      - {type: brief, ref: "old-manual.docx §3.1"}   # from the developer's brief
    steps:                           # replayed from the start state; one action per step
      - id: s1
        screen: orders               # links the step to the Screen Reference
        action: {action: click, target: {by: testid, value: new-order}}
        text: Click **New order**.
        highlight: true              # outline the acted-on element (default)
        crop: false                  # crop around the element (small targets in big windows)
troubleshooting:
  - {message: "Quantity must be greater than 0", source: lib/validate.js, cause: ..., fix: ...}
briefGaps:                           # brief items the current app does not have; listed in the run report
  - {item: Print a quote, source: "old-manual.docx §Printing", reason: no print feature in the current app}
```

## Actions

`goto` (web: path or URL), `click`, `double_click`, `type` (`value`, may use `${ENV}`), `select`
(`value` = option label or value), `press` (`value` such as `Enter`, `Escape`, `Control+S`, with or without a target), `hover`,
`wait` (`value` ms, or a target to wait for), `screenshot` (no-op), `close` (web: Escape; desktop: close the top window).
Optional: `timeoutMs`, `redact: [selectors]` (extra regions to blur for this step).

Targets, most stable first:

| Web | Desktop |
|---|---|
| `{by: testid, value}` | `{by: automation_id, value}` |
| `{by: role, value: button, name: Save}` | `{by: name, value: Save}` |
| `{by: label, value: Email}` | `{by: control_type, value: MenuItem, name: Customers}` |
| `{by: text, value}` | `{by: path, value: File/Options...}` (menu path, click only) |
| `{by: css, value}` (last resort) | |

## Screenshot timing

click, double_click, hover, select and press are shot **before** the action, with the element highlighted: the
screenshot shows what to click. type is shot **after** typing, with the field highlighted. Other actions are shot after.
