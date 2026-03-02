# =============================================================================
# scripts/install-voice-bridge.ps1 — Agentium voice bridge installer (Windows)
# Reads $env:USERPROFILE\.agentium\env.conf written by detect-host.ps1
# =============================================================================

$ErrorActionPreference = "Continue"

$CONF_DIR = Join-Path $env:USERPROFILE ".agentium"
$CONF_FILE = Join-Path $CONF_DIR "env.conf"
$LOG_FILE = Join-Path $CONF_DIR "install.log"
$VENV_DIR = Join-Path $CONF_DIR "voice-venv"
# $PSScriptRoot is scripts/ → one level up is repo root
$REPO_ROOT = Split-Path $PSScriptRoot -Parent
$BRIDGE_DIR = Join-Path $REPO_ROOT "voice-bridge"

New-Item -ItemType Directory -Force -Path $CONF_DIR | Out-Null

# ── helpers ───────────────────────────────────────────────────────────────────
function Write-Log($msg) {
    $ts = Get-Date -Format "HH:mm:ss"
    $line = "[$ts] $msg"
    Add-Content -Path $LOG_FILE -Value $line
    Write-Host $line
}

function Write-Warn($msg) {
    $line = "[WARN] $msg"
    Add-Content -Path $LOG_FILE -Value $line
    Write-Warning $line
}

function Run-Or-Warn($label, $scriptBlock) {
    try {
        & $scriptBlock 2>&1 | Tee-Object -FilePath $LOG_FILE -Append
        Write-Log "  ✓ $label"
        return $true
    } catch {
        Write-Warn "$label failed: $_"
        return $false
    }
}

# ── Load env.conf ─────────────────────────────────────────────────────────────
if (-not (Test-Path $CONF_FILE)) {
    Write-Warn "env.conf not found — run detect-host.ps1 first"
    exit 1
}

$conf = @{}
Get-Content $CONF_FILE | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
        $conf[$matches[1]] = $matches[2]
    }
}

$OS_FAMILY = $conf["OS_FAMILY"]
$PKG_MGR = $conf["PKG_MGR"]
$PYTHON_BIN = $conf["PYTHON_BIN"]
$SVC_MGR = $conf["SVC_MGR"]
$BACKEND_URL = $conf["BACKEND_URL"]

Write-Log "=== Agentium Voice Bridge Installer (Windows) ==="
Write-Log "OS_FAMILY=$OS_FAMILY  PKG_MGR=$PKG_MGR  PYTHON_BIN=$PYTHON_BIN"

# ── Step 2.1  System audio packages ───────────────────────────────────────────
Write-Log "Step 2.1 — Windows audio subsystem"
# No system packages needed on Windows — PyAudio includes PortAudio
Write-Log "  ✓ PyAudio includes precompiled PortAudio for Windows"

# ── Step 2.2  Python venv ─────────────────────────────────────────────────────
Write-Log "Step 2.2 — Creating Python venv at $VENV_DIR"
if ($PYTHON_BIN -eq "python3_missing") {
    Write-Warn "Python ≥ 3.10 not found — skipping venv and pip installs"
} else {
    Run-Or-Warn "create venv" { 
        & $PYTHON_BIN -m venv $VENV_DIR 
    }

    # Step 2.3 — pip install
    Write-Log "Step 2.3 — Installing Python packages"
    $VENV_PIP = Join-Path $VENV_DIR "Scripts\pip.exe"
    
    Run-Or-Warn "pip upgrade" { & $VENV_PIP install --upgrade pip }
    Run-Or-Warn "install websockets" { & $VENV_PIP install "websockets>=12.0" }
    Run-Or-Warn "install SpeechRecog" { & $VENV_PIP install "SpeechRecognition>=3.10.4" }
    
    # PyAudio now has precompiled wheels for Windows — no pipwin needed [^8^]
    Run-Or-Warn "install PyAudio" { & $VENV_PIP install "PyAudio>=0.2.14" }
    
    Run-Or-Warn "install pyttsx3" { & $VENV_PIP install "pyttsx3>=2.90" }
    Run-Or-Warn "install python-jose" { & $VENV_PIP install "python-jose[cryptography]>=3.3.0" }

    # Write the venv path to env.conf (Windows uses Scripts\python.exe)
    $VENV_PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"
    Add-Content -Path $CONF_FILE -Value "VENV_PYTHON=$VENV_PYTHON"
}

# ── Step 3  Service registration ─────────────────────────────────────────────
Write-Log "Step 3 — Registering Windows service (SVC_MGR=$SVC_MGR)"

$VENV_PYTHON = Join-Path $VENV_DIR "Scripts\python.exe"
$BRIDGE_CMD = "`"$VENV_PYTHON`" `"$BRIDGE_DIR\main.py`""

switch ($SVC_MGR) {
    "task_scheduler" {
        $TaskName  = "AgentiumVoiceBridge"
        $LogFile   = Join-Path $CONF_DIR "voice-bridge.log"
        $MainPy    = Join-Path $BRIDGE_DIR "main.py"

        # Validate paths before registering
        if (-not (Test-Path $VENV_PYTHON)) {
            Write-Warn "venv Python not found at $VENV_PYTHON -- did pip install succeed?"
        }
        if (-not (Test-Path $MainPy)) {
            Write-Warn "main.py not found at $MainPy -- check REPO_ROOT path"
        }

        # Remove existing task if present
        Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue | Unregister-ScheduledTask -Confirm:$false

        # Wrap in cmd.exe to capture stdout+stderr to log file
        $cmdArgs = "/c `"`"$VENV_PYTHON`" `"$MainPy`" >> `"$LogFile`" 2>&1`""
        $action   = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $cmdArgs
        $trigger  = New-ScheduledTaskTrigger -AtLogon
        $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 0)

        # Run as current user (no admin needed)
        $principal = New-ScheduledTaskPrincipal -GroupId "Users" -RunLevel Limited

        Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings | Out-Null

        # Start immediately
        Start-ScheduledTask -TaskName $TaskName
        Start-Sleep -Seconds 2

        $state = (Get-ScheduledTask -TaskName $TaskName).State
        Write-Log "  Task '$TaskName' state: $state"
        Write-Log "  Bridge log: $LogFile"
        Write-Log "  Manage with: Get-ScheduledTask -TaskName '$TaskName'"
    }
    
    "nssm" {
        # Alternative: NSSM for service-style management (requires admin)
        Write-Warn "NSSM mode requires manual setup. Run as Administrator:"
        Write-Warn "  nssm install AgentiumVoiceBridge `"$VENV_PYTHON`""
        Write-Warn "  nssm set AgentiumVoiceBridge AppParameters `"$BRIDGE_DIR\main.py`""
        Write-Warn "  nssm start AgentiumVoiceBridge"
    }
    
    default {
        Write-Warn "Unknown service manager — start manually:"
        Write-Warn "  $BRIDGE_CMD"
        
        # Create startup script
        $STARTUP = Join-Path $CONF_DIR "start-voice-bridge.bat"
        "@echo off`n$BRIDGE_CMD" | Set-Content $STARTUP
        Write-Log "  Created manual startup script: $STARTUP"
    }
}

Write-Log "=== Installation complete. Check $LOG_FILE for any warnings. ==="