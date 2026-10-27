# PushPilot One-Command Windows Installer
# Installs PushPilot, suppresses script warnings, and automatically adds Python Scripts to PATH

$ErrorActionPreference = "Stop"

Write-Host "`n=== Installing PushPilot ===" -ForegroundColor Cyan

# 1. Install / Upgrade PushPilot suppressing script warning
python -m pip install --upgrade pushpilot --no-warn-script-location

# 2. Automatically detect and add Python User Scripts directory to Windows User PATH
try {
    $scriptsDir = python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"
    if (Test-Path $scriptsDir) {
        $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($userPath -notlike "*$scriptsDir*") {
            [Environment]::SetEnvironmentVariable("Path", "$userPath;$scriptsDir", "User")
            $env:Path = "$env:Path;$scriptsDir"
            Write-Host "✔ Automatically added $scriptsDir to your User PATH!" -ForegroundColor Green
        }
    }
} catch {
    # Non-critical if PATH check fails
}

Write-Host "`n🚀 PushPilot installed successfully!" -ForegroundColor Green
Write-Host "Try running: pushpilot`n" -ForegroundColor Cyan
