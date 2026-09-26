// Minimal Electron app used by the GuideGen Electron driver test.
const { app, BrowserWindow } = require("electron");
const path = require("node:path");

app.whenReady().then(() => {
  const win = new BrowserWindow({ width: 1280, height: 800, title: "Electron Notes" });
  win.setMenuBarVisibility(false);
  win.loadFile(path.join(__dirname, "index.html"));
});

app.on("window-all-closed", () => app.quit());
