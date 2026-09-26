# ASP.NET Core MVC and Razor Pages

## Where screens live
- **Razor Pages**: `Pages/**/*.cshtml` with `@page` (route = folder path, or the `@page "/custom"` template).
  `_Layout`, `_ViewStart`, `_ViewImports` and partials (`_*.cshtml`) are not screens.
- **MVC**: controller actions returning `View()` → `Views/<Controller>/<Action>.cshtml`. The route comes from
  attribute routes (`[Route]`, `[HttpGet("...")]`) or the conventional `{controller}/{action}/{id?}`.
- Areas: `Areas/<Area>/Pages|Views`. Identity UI: `Areas/Identity/Pages/Account/*` (sign-in screens).
- Guards: `[Authorize(Roles=...)]`, `AuthorizeFolder` conventions in `Program.cs`.

## Dialogs and overlays
Bootstrap modals (`class="modal"`) in views or partials with forms: document as `dialog` screens.

## Navigation hints
`asp-page` / `asp-controller`/`asp-action` tag helpers in `_Layout.cshtml` nav; `RedirectToPage/Action` after POST.

## source
`.cshtml` + `.cshtml.cs` PageModel (or the controller + view) + the view model with DataAnnotations.

## Pitfalls
POST-only handlers are not screens. `Error.cshtml` / `Privacy.cshtml` templates only count if the product keeps them.
