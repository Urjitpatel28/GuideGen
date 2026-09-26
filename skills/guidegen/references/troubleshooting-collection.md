# Troubleshooting entries

Collect the **user-facing** error and validation messages from the code (aim for at least 5, up to about 25):

| Stack | Where to look |
|---|---|
| Web (any) | validation modules/schemas (zod, yup, joi, class-validator), `setError(...)`, form error components, toast/alert calls, API error bodies returned to the UI, i18n files (`en.json`) |
| ASP.NET | `[Required(ErrorMessage=...)]` and other DataAnnotations, `ModelState.AddModelError`, FluentValidation `.WithMessage`, `.resx` |
| WPF | `IDataErrorInfo` / `INotifyDataErrorInfo`, `ValidationRule`, `MessageBox.Show`, error TextBlocks, `.resx` |
| WinForms | `MessageBox.Show`, `ErrorProvider.SetError`, validation labels, `.resx` |
| Electron | the web rows above, plus `dialog.showErrorBox` / `showMessageBox` |

For each entry:

```yaml
- message: Quantity must be greater than 0     # EXACT string as the user sees it
  source: lib/validate.js                      # file where it is defined
  cause: The **Quantity** is 0, empty or not a number.   # why, in user terms
  fix: Type **1** or more.                                # what to do, imperative
```

Skip developer-only errors (stack traces, "unexpected null", HTTP 500 bodies), duplicates and messages that
cannot happen through the UI. If a message is built from a template (`{0} is required`), write the most
common concrete form.
