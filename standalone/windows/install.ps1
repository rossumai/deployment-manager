# Installs this prd2 bundle for the current user. Works offline.
#
#   Double-click install.cmd, or run:  powershell -ExecutionPolicy Bypass -File install.ps1
#
# Copies the bundle to %LOCALAPPDATA%\Programs\prd2 and adds that folder to the user PATH.
# Safe to re-run: it replaces the previously installed bundle.

$ErrorActionPreference = "Stop"

$SourceDir = $PSScriptRoot.TrimEnd("\")
$InstallDir = Join-Path $env:LOCALAPPDATA "Programs\prd2"

if ($SourceDir -ne $InstallDir) {
    # Copy next to the old bundle first, so a failed copy leaves the old one working.
    $Staging = "$InstallDir.new"
    if (Test-Path $Staging) { Remove-Item -Recurse -Force $Staging }
    New-Item -ItemType Directory -Force (Split-Path $InstallDir) | Out-Null
    Write-Host "Copying the bundle to $InstallDir ..."
    Copy-Item -Recurse $SourceDir $Staging
    if (Test-Path $InstallDir) { Remove-Item -Recurse -Force $InstallDir }
    Rename-Item $Staging (Split-Path -Leaf $InstallDir)
}

# Files unzipped from a download are marked as coming from the internet, which can trigger security prompts.
Get-ChildItem -Recurse -File $InstallDir | Unblock-File

# Prepended, so it wins over an older prd2 (e.g., one installed with uv).
# The registry keeps %VARIABLES% in PATH unexpanded, unlike [Environment]::SetEnvironmentVariable.
$Key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey("Environment", $true)
$UserPath = $Key.GetValue("Path", "", [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames)
$Entries = @($UserPath -split ";" | Where-Object { $_ -and $_.TrimEnd("\") -ne $InstallDir })
$Key.SetValue("Path", ((@($InstallDir) + $Entries) -join ";"), [Microsoft.Win32.RegistryValueKind]::ExpandString)
$Key.Close()
# Setting any user variable broadcasts the change, so terminals opened from now on see the new PATH.
[Environment]::SetEnvironmentVariable("PRD2_INSTALLER", "1", "User")
[Environment]::SetEnvironmentVariable("PRD2_INSTALLER", $null, "User")

if (Test-Path (Join-Path $env:USERPROFILE ".local\bin\prd2.exe")) {
    Write-Host "Note: an older prd2 installed with uv is still present. Remove it with:  uv tool uninstall deployment-manager"
}

$Version = & (Join-Path $InstallDir "prd2.cmd") --version
Write-Host "Installed $Version to $InstallDir"
Write-Host "Open a NEW terminal window and run:  prd2 --help"
