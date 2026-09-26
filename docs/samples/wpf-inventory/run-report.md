# GuideGen run report - Stockroom Inventory

Generated 2026-09-24 16:03 UTC · output folder `guidegen-out/`

## Summary

| Item | Count |
|---|---|
| Screens captured | 9 |
| Screens unreachable | 0 |
| Screens excluded (by you) | 0 |
| Screens cut by budget | 0 |
| Screens not yet captured | 0 |
| Tasks complete | 10 |
| Tasks with failed or refused steps | 0 |
| Tasks cut by budget | 0 |
| Troubleshooting entries | 10 |
| Refused destructive actions | 1 |
| Redactions applied | 13 |

## Captured

| Screen | Title | Image |
|---|---|---|
| `login-window` | Sign in | `screens/login-window.png` |
| `items` | Items tab | `screens/items.png` |
| `suppliers` | Suppliers tab | `screens/suppliers.png` |
| `reports` | Reports tab | `screens/reports.png` |
| `new-item` | New item window | `screens/new-item.png` |
| `receive-stock` | Receive stock window | `screens/receive-stock.png` |
| `categories` | Categories window | `screens/categories.png` |
| `settings` | Settings window | `screens/settings.png` |
| `about` | About window | `screens/about.png` |

## Unreachable

None - every inventoried screen was reached.

## Budget-cut

None.

## Tasks

| Rank | Task | Status | Evidence | Problem steps |
|---|---|---|---|---|
| 1 | `sign-in` Sign in | captured | ui-test | - |
| 2 | `add-item` Add a new item | captured | ui-test | - |
| 3 | `receive-delivery` Record a delivery | captured | ui-test | - |
| 4 | `edit-item` Change an item's details | captured | code | - |
| 5 | `find-item` Find an item | captured | ui-test | - |
| 6 | `check-low-stock` See what needs reordering | captured | code | - |
| 7 | `change-threshold` Change the low-stock level | captured | form-dependency | - |
| 8 | `add-category` Add a category | captured | form-dependency | - |
| 9 | `view-suppliers` Look up a supplier | captured | code | - |
| 10 | `delete-item` Delete an item | captured | code | s2: refused ('Delete' looks destructive (matches 'delete'). Refused by the engine; add it to safety.allowDestructive in guidegen.config.json if it is safe on this local app.) |

## Refused destructive actions

These were blocked by the engine. The step is documented from code with a screenshot of the state before the click.

- task delete-item step s2: `click automation_id=DeleteItemButton` - 'Delete' looks destructive (matches 'delete'). Refused by the engine; add it to safety.allowDestructive in guidegen.config.json if it is safe on this local app.

## Redactions

13 region(s) blurred across 8 image(s). Values are never recorded.

- `screens/login-window.png`: 1
- `screens/suppliers.png`: 6
- `screens/settings.png`: 1
- `screens/sign-in/s1.png`: 1
- `screens/sign-in/s2.png`: 1
- `screens/sign-in/s3.png`: 1
- `screens/change-threshold/s3.png`: 1
- `screens/change-threshold/s4.png`: 1

## Limitations

- Text drawn inside images, charts or custom-drawn controls cannot be detected for redaction. Use seed data with fake values and review screenshots before publishing.

## How to fix

Edit `manual.yaml` in the output folder, then run `/guidegen --update`:

- **Wrong or missing text** - set `override:` on the screen (`text.override`), task, step or troubleshooting entry. Overrides always win and are never touched by GuideGen.
- **Screen you do not want** - set `exclude: true`.
- **Unreachable screen** - add working `navigate:` steps (see references/manual-schema.md) and set `status: pending`.
- **Refused action that is safe** - add the button name to `safety.allowDestructive` in `guidegen.config.json`.
- **Text you edited directly** - add the field name to `locked:` on that item so regeneration keeps it.
- **Budget cuts** - raise `budget.maxScreens` / `budget.maxTasks`.
