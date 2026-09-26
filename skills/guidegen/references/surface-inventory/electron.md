# Electron

## Where screens live
- **Renderer**: apply the recipe for its web framework (React Router, Vue, Angular...) to the renderer source.
- **Windows**: every `new BrowserWindow(...)` in the main process (`main.js`, `electron/main.ts`) with the file or URL it
  loads. Secondary windows (Preferences, About) are screens (`kind: window`).
- **Native dialogs** (`dialog.showOpenDialog`, `showMessageBox`) are OS dialogs: document them from code and do not capture them.

## Commands and menus
`Menu.buildFromTemplate([...])` application and context menus (labels, `click`, `accelerator`), and IPC
handlers (`ipcMain.handle`) that open windows.

## Navigation hints
The engine starts Electron with `--remote-debugging-port` and drives the first window like a web page
(testid/role/label targets). Hash routes: `goto` with `#/route` relative to the start page.
Native application menus are not in the DOM: reach those screens through in-app UI or keyboard shortcuts (`press`).

## source
Renderer component files, plus the `BrowserWindow` creation site for extra windows.

## Pitfalls
`app.start` must launch the app from source (`npx electron .`), not a packaged installer.
