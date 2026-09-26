# SvelteKit

## Where screens live
- Every `src/routes/**/+page.svelte` is a route. The folder path is the URL: `(group)` folders are not in the URL,
  `[id]` is a parameter, `[[optional]]` an optional parameter, `[...rest]` a catch-all.
- `+page.ts` / `+page.server.ts` next to it load the page's data. Their `redirect(...)` calls and
  `hooks.server.(js|ts)` (`handle`) show login guards and role checks.
- A plain Svelte + Vite app without `@sveltejs/kit` has no file routes: follow the router it uses
  (`svelte-spa-router`, `svelte-routing`) as in [react-router](react-router.md).

## Dialogs and overlays
- Components with `<dialog>`, `Modal`/`Dialog`/`Drawer`/`Sheet` from UI kits (Skeleton, shadcn-svelte, Flowbite,
  Bits UI). An `open` prop or `bind:open` shows where they are triggered.
- Shallow routing (`pushState` / `replaceState` from `$app/navigation` with `page.state`) often opens a modal
  over a list: treat it as a dialog screen.
- A dialog becomes its own screen (`kind: dialog`) when it has fields or several actions. Otherwise document it as an element.

## Navigation hints
- Layouts (`+layout.svelte`) hold the nav: `<a href>` links and `goto(...)` calls.
- Form actions (`+page.server.ts` `actions`) with `use:enhance` show where a form redirects after success.
- Pick a real id from the seed data for `[id]` routes.

## source
`[src/routes/orders/+page.svelte, src/routes/orders/+page.server.ts, src/lib/components/OrderTable.svelte]`, plus
the schema or validation module the form action uses.

## Pitfalls
- `+error.svelte`, `+layout.*` and `+server.(js|ts)` (API endpoints) are not screens, except a custom error page users do see.
- Routes under `src/routes/api/**` are endpoints.
- `+page.ts` with `export const prerender = true` is still a screen; `ssr = false` pages need the app running to render.
