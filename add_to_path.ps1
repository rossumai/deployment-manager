Write-Host "Detecting Python installation..."

# Find the Python user base
$pythonUserBase = python -m site --user-base
$scriptsPath = "$pythonUserBase\Scripts"

# Override with actual known location if necessary
if (!(Test-Path "$scriptsPath")) {
    Write-Host "Python's reported Scripts directory not found. Checking known locations..."

    # Check if Python is installed in Local Programs
    $localPython = "C:\Users\$env:USERNAME\AppData\Local\Programs\Python"
    if (Test-Path "$localPython") {
        $pythonDir = Get-ChildItem -Path "$localPython" -Directory | Select-Object -ExpandProperty FullName -First 1
        if ($pythonDir) {
            $scriptsPath = "$pythonDir\Scripts"
            Write-Host "Using detected Python scripts path: $scriptsPath"
        }
    }
}

# Ensure the directory exists
if (!(Test-Path "$scriptsPath")) {
    Write-Host "Scripts directory not found: $scriptsPath"
    exit 1
}

# Add Scripts path to User PATH if not already added
$envPath = [System.Environment]::GetEnvironmentVariable("Path", "User")
if ($envPath -notlike "*$scriptsPath*") {
    Write-Host "Adding $scriptsPath to PATH..."
    [System.Environment]::SetEnvironmentVariable("Path", "$envPath;$scriptsPath", [System.EnvironmentVariableTarget]::User)
    Write-Host "PATH updated. Restart your terminal to apply changes."
} else {
    Write-Host "PATH is already set correctly."
}

# Check if prd2.exe exists
if (Test-Path "$scriptsPath\prd2.exe") {
    Write-Host "prd2 is now available globally. Try running 'prd2 --help'."
} else {
    Write-Host "prd2.exe not found. Try reinstalling with:"
    Write-Host "   pip install --user deployment-manager"
}

Write-Host "Done."
