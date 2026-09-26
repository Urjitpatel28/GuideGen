# WPF

## Where screens live
- **Windows**: every `*.xaml` whose root is `<Window>` (plus its `.xaml.cs`). Find how each is opened:
  `new XWindow().Show()/ShowDialog()`, `App.xaml` `StartupUri`, `OnStartup`.
- **Tabs and pages**: `TabItem`s in a window (`kind: tab`), `Frame.Navigate(new XPage())`, `UserControl`s swapped by
  a `ContentControl` bound to the current view model (MVVM navigation: look for `DataTemplate DataType=` mapping
  view models to views, and a `CurrentViewModel` property).
- **Dialogs**: windows opened with `ShowDialog()` → `kind: dialog`. `MessageBox.Show` texts go to Troubleshooting, not screens.

## Commands and menus
`<Menu>`/`<MenuItem Header Command>`, toolbar buttons, `InputBindings`/`KeyBinding`, and `ICommand`
properties in view models (`RelayCommand`, `DelegateCommand`, `[RelayCommand]` attributes from CommunityToolkit).

## Navigation hints (desktop targets)
- Prefer `AutomationProperties.AutomationId`. Otherwise `x:Name` (exposed as the AutomationId) or the button text (`name`).
- Menus: click the top-level `MenuItem`, then the item. Tabs: click the `TabItem`.
- DataGrid rows are named by the item's `ToString()`.

## source
`View.xaml`, `View.xaml.cs`, the view model, and validation (`IDataErrorInfo`, `ValidationRule`s).

## Pitfalls
- A login window shown before the main window needs `beforeLogin: true`.
- Controls without automation peers (custom `FrameworkElement` drawing, `Viewport3D`, WindowsFormsHost content) show as `(no-uia)`.
