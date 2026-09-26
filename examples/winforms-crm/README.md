# winforms-crm (GuideGen example)

"ClientDesk", a small WinForms CRM: sign-in form, main form with Customers / Activities / Dashboard tabs,
a MenuStrip, and New/Edit customer, Log activity, Options and About dialogs. Forms are built in code
(no designer files); every control has a `Name`, which WinForms exposes as the UI Automation AutomationId.
Fake data is seeded in memory on every start.

```
dotnet build src/Crm/Crm.csproj
src/Crm/bin/Debug/net9.0-windows/ClientDesk.exe
```

Demo login (fake account, safe to publish):

```
GUIDEGEN_USER=demo
GUIDEGEN_PASSWORD=clientdesk
```

What it exercises in GuideGen:

- a password `TextBox` (`UseSystemPasswordChar`) that is redacted
- ToolStrip menus (popup windows) captured over their window
- DataGridView rows, targeted by UIA name (`Name Row 2, Not sorted.`); numeric runtime ids are hidden from `tree`
- a custom-drawn chart (`SalesChart.cs`) with no UI Automation children, reported as a limitation
- the **Delete** button, which the engine refuses
- customer emails, which are redacted
- validation messages for Troubleshooting (`Data.cs` → `Messages`)
