# Blazor (Server / Web App / WebAssembly)

## Where screens live
- Every `.razor` component with `@page "/route"` (several `@page` lines mean several routes for one screen).
  Usually under `Components/Pages/` or `Pages/`.
- Guards: `@attribute [Authorize]`, `<AuthorizeView>` sections (document which parts need a role).

## Dialogs and overlays
MudBlazor `IDialogService.Show<T>()`, Radzen `DialogService.OpenAsync<T>()`, Fluent UI dialogs, or custom
components toggled by a bool.

## Navigation hints
`<NavLink href>` in `NavMenu.razor`; `NavigationManager.NavigateTo()`.

## source
The `.razor` file, `.razor.cs` code-behind, and the model with validation attributes (`<DataAnnotationsValidator/>`).

## Pitfalls
Interactive render modes: content can appear after load, so explore with `wait` on a target, not a fixed delay.
