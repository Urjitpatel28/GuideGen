# Angular

## Where screens live
- `Routes` arrays (`app.routes.ts`, `*-routing.module.ts`, `provideRouter(routes)`). Each `path` + `component`
  (or `loadComponent`) is a screen. `loadChildren` points to more route files, so follow it.
- Guards: `canActivate` / `canMatch` (auth, roles). Note which screens need which role.

## Dialogs and overlays
- `MatDialog.open(SomeDialogComponent)`, CDK overlays, `ngx-bootstrap` modals. A component opened this way with
  fields is a `dialog` screen.

## Navigation hints
- `routerLink` in nav or sidenav templates (`*.component.html`); `router.navigate([...])` after save.

## source
`*.component.ts` + `*.component.html` (+ the form group / validators file).

## Pitfalls
Standalone components and modules can coexist, so search both. Wildcard `**` routes are 404 pages.
