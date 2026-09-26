# Surface inventory recipes

One recipe per framework. Each says where screens are defined, how to find menus, commands and dialogs,
and what to put in `source`. Pick the recipe that matches `framework` in `.work/detect.json`, and a second
one for mixed stacks.

Goal: **every** user-facing screen that exists in code becomes a `screens` entry (target 100%). Skip
developer-only pages (storybook, `/_debug`, health checks, admin tools the customer never sees), error
boundaries and loading skeletons. An error page that users do see (404) can be a screen.

Each entry: `id` (kebab-case), `title` (as the user sees it), `kind`, `source` (all files whose change
alters the screen: page or view, its main component or view model, validation), no `navigate` yet.

Recipes: [nextjs](nextjs.md) · [sveltekit](sveltekit.md) · [react-router](react-router.md) · [angular](angular.md) · [vue](vue.md) ·
[aspnet-mvc-razor](aspnet-mvc-razor.md) · [blazor](blazor.md) · [wpf](wpf.md) · [winforms](winforms.md) ·
[winui](winui.md) · [electron](electron.md)

Contributing a framework: add `<framework>.md` with the same sections (Where screens live · Dialogs and
overlays · Navigation hints · source files · Pitfalls). No engine change is needed.
