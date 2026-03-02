# setup.ps1 — Windows entry point for Agentium Voice Bridge
# Usage: powershell -ExecutionPolicy Bypass -File setup.ps1

$ErrorActionPreference = "Stop"

$REPO_ROOT = Split-Path $PSScriptRoot -Parent

Write-Host "=== Agentium Voice Bridge Windows Installer ===" -ForegroundColor Cyan
Write-Host "Repo root: $REPO_ROOT"
Write-Host ""

# ── Phase 1: OS detection ──────────────────────────────────────────────────────
Write-Host "[setup.ps1] Running OS detection..." -ForegroundColor Yellow
$detectScript = Join-Path $REPO_ROOT "scripts\detect-host.ps1"
if (Test-Path $detectScript) {
    & $detectScript
} else {
    Write-Error "detect-host.ps1 not found at $detectScript"
}

# ── Phase 2+3: deps + service registration ───────────────────────────────────────
Write-Host "[setup.ps1] Running dependency installer..." -ForegroundColor Yellow
$installScript = Join-Path $REPO_ROOT "scripts\install-voice-bridge.ps1"
if (Test-Path $installScript) {
    & $installScript
} else {
    Write-Error "install-voice-bridge.ps1 not found at $installScript"
}

Write-Host ""
Write-Host "=== Voice bridge installation complete ===" -ForegroundColor Green
Write-Host "Check $env:USERPROFILE\.agentium\install.log for details."
Write-Host ""

# ── Verify the scheduled task actually started ────────────────────────────────
Write-Host "[setup.ps1] Verifying scheduled task..." -ForegroundColor Yellow
$task = Get-ScheduledTask -TaskName "AgentiumVoiceBridge" -ErrorAction SilentlyContinue
if ($task) {
    $state = $task.State
    Write-Host "  Task state: $state" -ForegroundColor $(if ($state -eq "Running") { "Green" } else { "Yellow" })
    if ($state -ne "Running") {
        Write-Host "  Starting task now..." -ForegroundColor Yellow
        Start-ScheduledTask -TaskName "AgentiumVoiceBridge"
        Start-Sleep -Seconds 2
        $state = (Get-ScheduledTask -TaskName "AgentiumVoiceBridge").State
        Write-Host "  Task state after start: $state" -ForegroundColor $(if ($state -eq "Running") { "Green" } else { "Red" })
    }
} else {
    Write-Warning "  AgentiumVoiceBridge task not found — check install.log"
}

Write-Host ""
Write-Host "To check status : Get-ScheduledTask -TaskName AgentiumVoiceBridge"
Write-Host "To start manually: Start-ScheduledTask -TaskName AgentiumVoiceBridge"
Write-Host "To view logs    : Get-Content `$env:USERPROFILE\.agentium\voice-bridge.log -Tail 50"