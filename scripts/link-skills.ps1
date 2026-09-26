# Creates the skill discovery links (.claude/.agents/.opencode -> skills/guidegen).
# Uses real symlinks when allowed (Developer Mode / admin); otherwise directory junctions, which work
# for local discovery but are not committed (they are added to .git/info/exclude).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$target = Join-Path $root "skills\guidegen"
foreach ($dir in ".claude\skills", ".agents\skills", ".opencode\skills") {
    $parent = Join-Path $root $dir
    New-Item -ItemType Directory -Force $parent | Out-Null
    $link = Join-Path $parent "guidegen"
    if (Test-Path $link) { Write-Output "exists: $dir\guidegen"; continue }
    try {
        New-Item -ItemType SymbolicLink -Path $link -Target "..\..\skills\guidegen" | Out-Null
        Write-Output "symlink: $dir\guidegen"
    } catch {
        New-Item -ItemType Junction -Path $link -Target $target | Out-Null
        $exclude = Join-Path $root ".git\info\exclude"
        if (Test-Path (Split-Path $exclude)) { Add-Content $exclude ("/" + ($dir -replace '\\', '/') + "/guidegen") }
        Write-Output "junction (not committed): $dir\guidegen"
    }
}
