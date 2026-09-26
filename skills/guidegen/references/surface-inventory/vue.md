# Vue (Vite / Vue CLI / Nuxt)

## Where screens live
- Vue Router: `router/index.(js|ts)` `routes: [{ path, component }]`, including lazy `() => import('...')`.
- Nuxt: `pages/**/*.vue` file routes (`[id].vue` = parameter, `index.vue` = folder root).
- Guards: `router.beforeEach`, route `meta.requiresAuth`, Nuxt `middleware/`.

## Dialogs and overlays
- `<el-dialog>`, `<v-dialog>`, `<q-dialog>`, `<Dialog>` (PrimeVue) and `v-model:visible` flags.

## Navigation hints
`<router-link to>` / `<NuxtLink>` in layout components; `router.push()` after actions.

## source
The `.vue` single-file component (template + script) and any `composables/` or validation it uses.

## Pitfalls
Nuxt `layouts/` and `app.vue` are shells, not screens.
