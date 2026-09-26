# WinUI 3 (Windows App SDK)

## Where screens live
- `Window` XAML files (`MainWindow.xaml`), and `Page`s navigated in a `Frame` (`ContentFrame.Navigate(typeof(XPage))`),
  usually from a `NavigationView` (`NavigationViewItem Tag="..."` mapped to page types).
- `ContentDialog`s (`await dialog.ShowAsync()`) → `kind: dialog`.

## Commands and menus
`NavigationView` items, `CommandBar`/`AppBarButton`, `MenuBar`, `MenuFlyout`, `XamlUICommand`.

## Navigation hints (desktop targets)
`AutomationProperties.AutomationId` or `x:Name`; `NavigationViewItem` by `name`. ContentDialogs appear as
child elements of the window: use `tree` to find their buttons.

## source
`XPage.xaml` + `.xaml.cs` + view model.

## Pitfalls
- **Packaged (MSIX) apps** cannot be launched from the .exe path. Set `app.start` to launch via
  `explorer.exe shell:AppsFolder\<PackageFamilyName>!App`, or build unpackaged (`WindowsPackageType=None`).
  If that fails, raise a `start` blocker.
- WinUI support is new in GuideGen v1 and not covered by an example app yet; report rough edges.
