# Next.js

## Where screens live
- **App Router**: every `app/**/page.(js|jsx|ts|tsx)` is a route. The folder path is the URL: `(group)` folders are
  not in the URL, `[id]` is a parameter, `[...slug]` a catch-all, `@slot` a parallel route.
- **Pages Router**: `pages/**/*.(js|tsx)` except `_app`, `_document`, `api/**`.
- Route guards: `middleware.(js|ts)` (login redirects, role checks) and `layout.*` files that redirect.

## Dialogs and overlays
- Components rendering `<dialog>`, `Dialog`/`Modal`/`Sheet`/`Drawer` from UI kits (shadcn, MUI, Radix). Opening
  state (`useState(open)`) shows where they are triggered. Intercepting routes `(.)foo` are modal screens.
- A dialog becomes its own screen (`kind: dialog`) when it has fields or several actions. Otherwise document it as an element.

## Navigation hints
- Nav components (`Nav`, `Sidebar`, `Header`) with `Link href`. `useRouter().push(...)` after form success.
- Pick a real id from the seed data for `[id]` routes.

## source
`[app/orders/page.js, app/orders/OrderTable.tsx, lib/validation/order.ts]`, plus the API route file when the page's behaviour is defined there.

## Pitfalls
- `loading.js`, `error.js`, `not-found.js`, `template.js` are not screens (except a custom `not-found` users do see).
- `app/api/**` and `route.(js|ts)` are endpoints, not screens.
