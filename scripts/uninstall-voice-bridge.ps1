# scripts/uninstall-voice-bridge.ps1
# Stops and removes the voice bridge service on Windows

$ErrorActionPreference = "Continue"

$CONF_FILE = Join-Path $env:USERPROFILE ".agentium\env.conf"

function Write-Log($msg) {
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $msg"
}

function Write-Warn($msg) {
    Write-Warning "[WARN] $msg"
}

if (-not (Test-Path $CONF_FILE)) {
    Write-Warn "env.conf not found — nothing to uninstall"
    exit 0
}

$conf = @{}
Get-Content $CONF_FILE | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        $conf[$matches[1]] = $matches[2]
    }
}

$SVC_MGR = $conf["SVC_MGR"]

Write-Log "=== Agentium Voice Bridge Uninstaller (Windows) ==="

switch ($SVC_MGR) {
    "task_scheduler" {
        $TaskName = "AgentiumVoiceBridge"
        Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false
        Write-Log "Task Scheduler task '$TaskName' removed"
    }
    
    "nssm" {
        $serviceName = "AgentiumVoiceBridge"
        if (Get-Service $serviceName -ErrorAction SilentlyContinue) {
            nssm stop $serviceName 2>$null
            nssm remove $serviceName confirm 2>$null
            Write-Log "NSSM service '$serviceName' removed"
        }
    }
    
    default {
        # Kill any running Python processes for the bridge
        Get-Process python -ErrorAction SilentlyContinue | Where-Object { 
            $_.CommandLine -like "*voice-bridge*" 
        } | Stop-Process -Force
        Write-Log "Bridge processes stopped"
    }
}

Write-Log "Venv and conf files left in $env:USERPROFILE\.agentium (remove manually if desired)"
Write-Log "=== Uninstall complete ==="