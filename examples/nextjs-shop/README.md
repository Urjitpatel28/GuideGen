# nextjs-shop (GuideGen example)

A small Next.js back-office for a coffee shop: dashboard, products, orders, customers and settings.
All data is fake and lives in `data/db.json` (reset with `npm run seed`).

```
npm install
npm run seed
npm run dev        # http://localhost:3210
```

Demo login (fake account, safe to publish):

```
GUIDEGEN_USER=demo@shop.test
GUIDEGEN_PASSWORD=demo1234
```

What it exercises in GuideGen:

- login + seed data, 11 screens (`expected-screens.json`)
- form dependencies (an order needs a customer and a product)
- validation messages for the Troubleshooting chapter (`lib/validate.js`)
- destructive buttons the engine must refuse: **Delete product**, **Send invoice**
- email addresses on screen that must be redacted (Customers, Order detail, the signed-in user)
- Playwright E2E tests in `tests/e2e/` used as task evidence
