# One-command installer for the Rossum deployment manager (prd2) on Windows.
#
#   powershell -ExecutionPolicy ByPass -c "irm https://raw.githubusercontent.com/rossumai/deployment-manager/main/install.ps1 | iex"
#
# Install a specific version by setting PRD_VERSION first:
#
#   $env:PRD_VERSION = "v2.7.0a"; irm https://raw.githubusercontent.com/rossumai/deployment-manager/main/install.ps1 | iex
#
# Uses uv (https://docs.astral.sh/uv/), which brings its own Python 3.12 and
# keeps prd2 in an isolated environment, so nothing else needs to be installed.
# Safe to re-run: it upgrades an existing installation.

& {
    # Keep the preference and variables out of the user's session (this runs via iex).
    $ErrorActionPreference = "Stop"
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12

    $Repo = "rossumai/deployment-manager"
    $DownloadPrefix = "https://github.com/$Repo/releases/download/"

    # uv version used when this installer has to install uv itself. Bumped manually;
    # it does not affect an already installed uv.
    $UvVersion = "0.13.1"

    # Always x64 Python: ruamel-yaml-clib (pulled in by ruamel-yaml <0.19) publishes
    # no Windows ARM64 wheels, and Windows 11 on ARM runs x64 Python under emulation.
    $Python = "cpython-3.12-windows-x86_64-none"

    # The tag ends up in a URL, so accept only things that look like a version tag.
    if ($env:PRD_VERSION -and $env:PRD_VERSION -cnotmatch '^v[0-9][A-Za-z0-9._-]*$') {
        Write-Host "Error: Invalid version tag: $env:PRD_VERSION" -ForegroundColor Red
        return
    }

    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            Write-Host "Git is missing. Installing it via winget..."
            winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
            $env:Path = "$env:ProgramFiles\Git\cmd;$env:Path"
        }
        if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
            Write-Host "Error: Git is required but not installed." -ForegroundColor Red
            Write-Host "Install it from https://git-scm.com/downloads/win, then open a new terminal and run this installer again."
            return
        }
    }

    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "Installing uv $UvVersion (Python package manager). Its installer may add uv to your user PATH."
        Invoke-RestMethod "https://astral.sh/uv/$UvVersion/install.ps1" | Invoke-Expression
        $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
        if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
            Write-Host "Error: uv was installed but could not be found. Open a new terminal and run this installer again." -ForegroundColor Red
            return
        }
    }

    if ($env:PRD_VERSION) {
        $ApiUrl = "https://api.github.com/repos/$Repo/releases/tags/$env:PRD_VERSION"
    } else {
        $ApiUrl = "https://api.github.com/repos/$Repo/releases/latest"
    }

    Write-Host "Looking up the release..."
    try {
        $Release = Invoke-RestMethod -Uri $ApiUrl
    } catch {
        Write-Host "Error: Could not find the release ($ApiUrl)." -ForegroundColor Red
        return
    }
    $WheelUrl = $Release.assets | Where-Object { $_.name -like "*.whl" } | Select-Object -First 1 -ExpandProperty browser_download_url
    if (-not $WheelUrl) {
        Write-Host "Error: No installable release found." -ForegroundColor Red
        return
    }

    $ShaUrl = $Release.assets | Where-Object { $_.name -like "*.whl.sha256" } | Select-Object -First 1 -ExpandProperty browser_download_url
    if (-not $ShaUrl) {
        Write-Host "Error: Refusing to install: no checksum published for this release." -ForegroundColor Red
        return
    }
    foreach ($Url in @($WheelUrl, $ShaUrl)) {
        if (-not $Url.StartsWith($DownloadPrefix)) {
            Write-Host "Error: Unexpected download URL: $Url" -ForegroundColor Red
            return
        }
    }

    # The wheel keeps its original filename because uv validates it.
    $TmpDir = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName())
    New-Item -ItemType Directory -Path $TmpDir | Out-Null
    try {
        $WheelFile = Join-Path $TmpDir ($WheelUrl.Split("/")[-1])
        $ShaFile = Join-Path $TmpDir "checksum.sha256"

        Write-Host "Downloading $WheelUrl"
        try {
            Invoke-WebRequest -Uri $WheelUrl -OutFile $WheelFile -UseBasicParsing
            Invoke-WebRequest -Uri $ShaUrl -OutFile $ShaFile -UseBasicParsing
        } catch {
            Write-Host "Error: Could not download the release files." -ForegroundColor Red
            return
        }

        # The checksum file is in `sha256sum` format: "<hash>  <filename>".
        $Expected = ((Get-Content -Path $ShaFile -TotalCount 1) -split '\s+')[0]
        $Actual = (Get-FileHash -Path $WheelFile -Algorithm SHA256).Hash
        if (-not $Expected -or $Expected -ne $Actual) {
            Write-Host "Error: Checksum mismatch for $($WheelUrl.Split('/')[-1]): expected $Expected, got $Actual. Aborting." -ForegroundColor Red
            return
        }
        Write-Host "Checksum OK."

        uv tool install --force --python $Python $WheelFile
        if ($LASTEXITCODE -ne 0) {
            Write-Host "Error: installation failed." -ForegroundColor Red
            return
        }
    } finally {
        Remove-Item -Path $TmpDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Adds uv's tool directory to the user PATH if it is not there yet.
    # uv writes its status to stderr, which Windows PowerShell 5.1 turns into a terminating error under "Stop".
    try { uv tool update-shell *> $null } catch {}

    Write-Host ""
    Write-Host "Done! Open a NEW terminal window and run:  prd2 --help"
}
