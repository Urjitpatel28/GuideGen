# WinForms

## Where screens live
- Every class deriving from `Form` (`*.cs` + `*.Designer.cs`), and how it is opened: `Application.Run(new MainForm())`,
  `new XForm().ShowDialog(this)` (`kind: dialog`) or `.Show()`.
- `TabPage`s inside a `TabControl` (`kind: tab`), `UserControl`s swapped into panels, MDI children.

## Commands and menus
`MenuStrip`/`ToolStripMenuItem` (Text and Click handlers), `ToolStrip` buttons, `ContextMenuStrip`, shortcut keys.

## Navigation hints (desktop targets)
- The control's `Name` is its UIA AutomationId (set in the Designer), so use `automation_id`.
- `ToolStripMenuItem`s have no AutomationId: target them by `name` (text without `&`), or with
  `{by: control_type, value: MenuItem, name: ...}` when the text also appears on a tab or button.
- DataGridView cells: `name` like `Name Row 2, Not sorted.` (rows start at 1). `tree` shows cell values.

## source
`XForm.cs` + `XForm.Designer.cs` (+ `.resx` for texts), plus the validation code (`ErrorProvider`, `MessageBox.Show`).

## Pitfalls
- Owner-drawn controls, charts, and `OnPaint` panels are `(no-uia)`: captured as part of the window and documented from code.
- Login forms shown before `Application.Run`: `beforeLogin: true`.
