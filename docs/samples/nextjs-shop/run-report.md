# GuideGen run report - Acme Shop

Generated 2026-09-24 15:42 UTC · output folder `guidegen-out/`

## Summary

| Item | Count |
|---|---|
| Screens captured | 11 |
| Screens unreachable | 0 |
| Screens excluded (by you) | 0 |
| Screens cut by budget | 0 |
| Screens not yet captured | 0 |
| Tasks complete | 10 |
| Tasks with failed or refused steps | 0 |
| Tasks cut by budget | 0 |
| Troubleshooting entries | 8 |
| Refused destructive actions | 1 |
| Redactions applied | 65 |

## Captured

| Screen | Title | Image |
|---|---|---|
| `login` | Sign in | `screens/login.png` |
| `dashboard` | Dashboard | `screens/dashboard.png` |
| `products` | Products | `screens/products.png` |
| `new-product` | New product | `screens/new-product.png` |
| `product-detail` | Product details | `screens/product-detail.png` |
| `orders` | Orders | `screens/orders.png` |
| `new-order` | New order | `screens/new-order.png` |
| `order-detail` | Order details | `screens/order-detail.png` |
| `customers` | Customers | `screens/customers.png` |
| `new-customer` | New customer | `screens/new-customer.png` |
| `settings` | Settings | `screens/settings.png` |

## Unreachable

None - every inventoried screen was reached.

## Budget-cut

None.

## Tasks

| Rank | Task | Status | Evidence | Problem steps |
|---|---|---|---|---|
| 1 | `sign-in` Sign in to Acme Shop | captured | e2e-test | - |
| 2 | `create-order` Create an order | captured | e2e-test, form-dependency | - |
| 3 | `add-customer` Add a customer | captured | e2e-test, form-dependency | - |
| 4 | `add-product` Add a product | captured | e2e-test | - |
| 5 | `adjust-stock` Correct the stock count | captured | e2e-test | - |
| 6 | `ship-order` Mark an order as shipped | captured | e2e-test | - |
| 7 | `send-invoice` Send an invoice | captured | code | s3: refused ('Send invoice' looks destructive (matches 'send'). Refused by the engine; add it to safety.allowDestructive in guidegen.config.json if it is safe on this local app.) |
| 8 | `change-settings` Change store settings | captured | e2e-test | - |
| 9 | `check-low-stock` Find products that are running low | captured | code | - |
| 10 | `sign-out` Sign out | captured | e2e-test | - |

## Refused destructive actions

These were blocked by the engine. The step is documented from code with a screenshot of the state before the click.

- task send-invoice step s3: `click role=button name=Send invoice` - 'Send invoice' looks destructive (matches 'send'). Refused by the engine; add it to safety.allowDestructive in guidegen.config.json if it is safe on this local app.

## Redactions

65 region(s) blurred across 51 image(s). Values are never recorded.

- `screens/login.png`: 1
- `screens/dashboard.png`: 1
- `screens/products.png`: 1
- `screens/new-product.png`: 1
- `screens/product-detail.png`: 1
- `screens/orders.png`: 1
- `screens/new-order.png`: 1
- `screens/order-detail.png`: 2
- `screens/customers.png`: 4
- `screens/new-customer.png`: 1
- `screens/settings.png`: 1
- `screens/sign-in/s1.png`: 1
- `screens/sign-in/s2.png`: 2
- `screens/sign-in/s3.png`: 2
- `screens/sign-in/s4.png`: 2
- `screens/create-order/s1.png`: 1
- `screens/create-order/s2.png`: 1
- `screens/create-order/s3.png`: 1
- `screens/create-order/s4.png`: 1
- `screens/create-order/s5.png`: 1
- `screens/create-order/s6.png`: 1
- `screens/add-customer/s1.png`: 1
- `screens/add-customer/s2.png`: 4
- `screens/add-customer/s3.png`: 1
- `screens/add-customer/s4.png`: 2
- `screens/add-customer/s5.png`: 2
- `screens/add-product/s1.png`: 1
- `screens/add-product/s2.png`: 1
- `screens/add-product/s3.png`: 1
- `screens/add-product/s4.png`: 1
- `screens/add-product/s5.png`: 1
- `screens/add-product/s6.png`: 1
- `screens/add-product/s7.png`: 1
- `screens/add-product/s8.png`: 1
- `screens/adjust-stock/s1.png`: 1
- `screens/adjust-stock/s2.png`: 1
- `screens/adjust-stock/s3.png`: 1
- `screens/adjust-stock/s4.png`: 1
- `screens/ship-order/s1.png`: 1
- `screens/ship-order/s2.png`: 1
- `screens/ship-order/s3.png`: 2
- `screens/send-invoice/s1.png`: 1
- `screens/send-invoice/s2.png`: 1
- `screens/send-invoice/s3.png`: 2
- `screens/change-settings/s1.png`: 1
- `screens/change-settings/s2.png`: 1
- `screens/change-settings/s3.png`: 1
- `screens/change-settings/s4.png`: 1
- `screens/check-low-stock/s1.png`: 1
- `screens/check-low-stock/s2.png`: 1
- `screens/sign-out/s1.png`: 1

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
