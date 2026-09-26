# GuideGen run report - ClientDesk CRM

Generated 2026-09-24 16:12 UTC · output folder `guidegen-out/`

## Summary

| Item | Count |
|---|---|
| Screens captured | 8 |
| Screens unreachable | 0 |
| Screens excluded (by you) | 0 |
| Screens cut by budget | 0 |
| Screens not yet captured | 0 |
| Tasks complete | 9 |
| Tasks with failed or refused steps | 0 |
| Tasks cut by budget | 0 |
| Troubleshooting entries | 8 |
| Refused destructive actions | 1 |
| Redactions applied | 74 |

## Captured

| Screen | Title | Image |
|---|---|---|
| `login-form` | Sign in | `screens/login-form.png` |
| `customers` | Customers tab | `screens/customers.png` |
| `activities` | Activities tab | `screens/activities.png` |
| `dashboard` | Dashboard tab | `screens/dashboard.png` |
| `customer-form` | New customer window | `screens/customer-form.png` |
| `activity-form` | Log activity window | `screens/activity-form.png` |
| `options` | Options window | `screens/options.png` |
| `about` | About window | `screens/about.png` |

## Unreachable

None - every inventoried screen was reached.

## Budget-cut

None.

## Tasks

| Rank | Task | Status | Evidence | Problem steps |
|---|---|---|---|---|
| 1 | `sign-in` Sign in | captured | code | - |
| 2 | `add-customer` Add a customer | captured | form-dependency | - |
| 3 | `log-activity` Log a call or meeting | captured | code | - |
| 4 | `edit-customer` Update a customer's details | captured | code | - |
| 5 | `find-customer` Find a customer | captured | code | - |
| 6 | `check-pipeline` Check your sales pipeline | captured | code | - |
| 7 | `review-activities` Review recent activities | captured | code | - |
| 8 | `set-default-status` Change the default status for new customers | captured | form-dependency | - |
| 9 | `delete-customer` Delete a customer | captured | code | s2: refused ('Delete' looks destructive (matches 'delete'). Refused by the engine; add it to safety.allowDestructive in guidegen.config.json if it is safe on this local app.) |

## Refused destructive actions

These were blocked by the engine. The step is documented from code with a screenshot of the state before the click.

- task delete-customer step s2: `click automation_id=DeleteCustomerButton` - 'Delete' looks destructive (matches 'delete'). Refused by the engine; add it to safety.allowDestructive in guidegen.config.json if it is safe on this local app.

## Redactions

74 region(s) blurred across 26 image(s). Values are never recorded.

- `screens/login-form.png`: 1
- `screens/customers.png`: 5
- `screens/options.png`: 1
- `screens/sign-in/s1.png`: 1
- `screens/sign-in/s2.png`: 1
- `screens/sign-in/s3.png`: 1
- `screens/add-customer/s1.png`: 5
- `screens/add-customer/s4.png`: 1
- `screens/add-customer/s5.png`: 1
- `screens/add-customer/s6.png`: 1
- `screens/add-customer/s7.png`: 1
- `screens/log-activity/s1.png`: 5
- `screens/log-activity/s2.png`: 5
- `screens/edit-customer/s1.png`: 5
- `screens/edit-customer/s2.png`: 5
- `screens/edit-customer/s3.png`: 1
- `screens/edit-customer/s4.png`: 1
- `screens/find-customer/s1.png`: 1
- `screens/check-pipeline/s1.png`: 5
- `screens/review-activities/s1.png`: 5
- `screens/set-default-status/s1.png`: 5
- `screens/set-default-status/s2.png`: 5
- `screens/set-default-status/s3.png`: 1
- `screens/set-default-status/s4.png`: 1
- `screens/delete-customer/s1.png`: 5
- `screens/delete-customer/s2.png`: 5

## Limitations

- Screen `dashboard` contains controls without UI Automation support; captured as a whole window and documented from code.
- control 'Pipeline chart' exposes no UI Automation children; captured as part of the window only
- Text drawn inside images, charts or custom-drawn controls cannot be detected for redaction. Use seed data with fake values and review screenshots before publishing.

## How to fix

Edit `manual.yaml` in the output folder, then run `/guidegen --update`:

- **Wrong or missing text** - set `override:` on the screen (`text.override`), task, step or troubleshooting entry. Overrides always win and are never touched by GuideGen.
- **Screen you do not want** - set `exclude: true`.
- **Unreachable screen** - add working `navigate:` steps (see references/manual-schema.md) and set `status: pending`.
- **Refused action that is safe** - add the button name to `safety.allowDestructive` in `guidegen.config.json`.
- **Text you edited directly** - add the field name to `locked:` on that item so regeneration keeps it.
- **Budget cuts** - raise `budget.maxScreens` / `budget.maxTasks`.
