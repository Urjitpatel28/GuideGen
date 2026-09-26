# React (Vite / CRA) with React Router

## Where screens live
- Route tables: `createBrowserRouter([...])`, `<Routes><Route path element/>`, `routes.tsx`, or file routes
  (`app/routes/*` in React Router v7 / Remix framework mode, TanStack Router `routes/`).
- Each `path` with an `element` / `Component` is a screen. Nested routes with `<Outlet/>` are separate screens
  when they change the main content.
- Guards: wrapper elements such as `<RequireAuth>` / `<ProtectedRoute>`, and loaders that `redirect()`.

## Dialogs and overlays
- `Modal`/`Dialog` components and `open` state; routes that render modals over a background (`state.backgroundLocation`).

## Navigation hints
- `<NavLink>`/`<Link to>` in layout components; `navigate('/x')` after actions.
- Hash routers (`createHashRouter`): URLs look like `/#/orders`, so use `goto` with `/#/orders`.

## source
Route element component, its data hooks or loaders, and form validation schema files.

## Pitfalls
Lazy routes (`lazy: () => import(...)`): follow the import to the real file.
