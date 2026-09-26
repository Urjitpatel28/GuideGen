# wpf-inventory (GuideGen example)

A WPF (MVVM) stockroom inventory app: sign-in window, main window with Items / Suppliers / Reports tabs,
menus, and New item, Receive stock, Categories, Settings and About dialogs. Fake data is seeded in memory
on every start, so every run looks the same.

```
dotnet build src/Inventory/Inventory.csproj
src/Inventory/bin/Debug/net9.0-windows/Inventory.exe
```

Demo login (fake account, safe to publish):

```
GUIDEGEN_USER=demo
GUIDEGEN_PASSWORD=stockroom
```

What it exercises in GuideGen:

- desktop sign-in with a `PasswordBox` (redacted) and `beforeLogin` capture of the sign-in window
- modal dialogs (exposed by UIA as child windows) and open menus captured over their window
- stable `AutomationProperties.AutomationId` targets everywhere
- validation messages for Troubleshooting (`ViewModels/Validation.cs`)
- the **Delete** button, which the engine refuses
- supplier emails and the report email address, which are redacted
- FlaUI UI tests in `tests/Inventory.UiTests` used as task evidence (`dotnet test tests/Inventory.UiTests`)
