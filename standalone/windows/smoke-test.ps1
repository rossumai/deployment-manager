# Smoke-tests an unzipped Windows bundle. It runs on Windows, since build.sh builds on macOS and cannot run Windows programs.
#
#   powershell -ExecutionPolicy Bypass -File standalone\windows\smoke-test.ps1 <unzipped bundle folder>

param([Parameter(Mandatory = $true)][string]$BundleDir)

$ErrorActionPreference = "Stop"
$BundleDir = (Resolve-Path $BundleDir).Path

# Runs a native program and fails the test when it fails, which PowerShell does not do by itself.
function Invoke-Native([string]$FilePath, [string[]]$Arguments) {
    # Native stderr output (e.g., git warnings) must not turn into a terminating PowerShell error.
    $ErrorActionPreference = "Continue"
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) { throw "$(Split-Path -Leaf $FilePath) failed with exit code $LASTEXITCODE." }
}

# Only Windows' own folders on PATH, like a machine without Python or Git.
$SystemPath = "$env:SystemRoot\System32;$env:SystemRoot;$env:SystemRoot\System32\Wbem;$env:SystemRoot\System32\WindowsPowerShell\v1.0"
$Git = Join-Path $BundleDir "git\cmd\git.exe"
$Work = Join-Path ([IO.Path]::GetTempPath()) ("prd2-smoke-" + [IO.Path]::GetRandomFileName())
New-Item -ItemType Directory $Work | Out-Null
$SavedPath, $SavedHome = $env:Path, $env:HOME
Push-Location $Work
try {
    $env:Path = $SystemPath
    # Keeps the tester's own git config out of the test
    $env:HOME = $Work
    Invoke-Native (Join-Path $BundleDir "prd2.cmd") @("--version")

    # prd2's modified_by clean filter runs sed through sh, both of which must come from the bundled Git.
    # PATH as the launcher sets it, so Python finds the bundled git.
    $env:Path = "$(Join-Path $BundleDir 'git\cmd');$SystemPath;$(Join-Path $BundleDir 'git\usr\bin')"
    Invoke-Native $Git @("init", "-q", "repo")
    Invoke-Native (Join-Path $BundleDir "python\python.exe") @("-I", "-c",
        "import anyio; from deployment_manager.commands.initialize import setup_modified_by_filter; anyio.run(setup_modified_by_filter, anyio.Path('repo'))")
    Set-Content -Path "repo\queue.json" -Encoding ASCII -Value @('{', '  "id": 1,', '  "modified_by": "https://x.rossum.app/api/v1/users/8"', '}')
    Invoke-Native $Git @("-C", "repo", "add", ".")
    Invoke-Native $Git @("-C", "repo", "-c", "user.name=smoke", "-c", "user.email=smoke@test", "commit", "-q", "-m", "smoke")
    $Committed = (Invoke-Native $Git @("-C", "repo", "show", "HEAD:queue.json")) -join "`n"
    if ($Committed -notmatch '"modified_by": null') { throw "The bundled Git did not apply prd2's modified_by filter." }

    Invoke-Native $Git @("ls-remote", "https://github.com/rossumai/deployment-manager", "HEAD") | Out-Null
}
finally {
    Pop-Location
    $env:Path, $env:HOME = $SavedPath, $SavedHome
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue $Work
}

Write-Host "Smoke test passed: $BundleDir"
