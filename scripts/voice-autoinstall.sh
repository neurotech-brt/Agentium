#!/usr/bin/env bash
# =============================================================================
# scripts/voice-autoinstall.sh
# Runs inside the voice-autoinstall Docker container.
# Detects the host OS and installs the voice bridge with zero manual steps.
#
# Unix hosts  (Linux / macOS / WSL2):
#   Installs Python deps + registers the OS service directly via the
#   mounted ~/.agentium volume. Bridge starts immediately.
#
# Windows hosts (Docker Desktop):
#   Cannot exec PowerShell on the host from a Linux container.
#   Instead, drops two files onto the host via the /host_home mount:
#     1. %USERPROFILE%\.agentium\bootstrap-voice.cmd
#          Calls setup.ps1 and logs to bootstrap.log
#     2. Startup folder\agentium-voice-startup.cmd
#          Runs bootstrap-voice.cmd silently on every Windows login
#   The bridge will start automatically on the user's next login.
#   To start immediately without logging out, the user just double-clicks
#   %USERPROFILE%\.agentium\bootstrap-voice.cmd  (printed at the end).
# =============================================================================
set -euo pipefail

MARKER=/root/.agentium/voice-installed.marker

echo "[voice-autoinstall] Backend is healthy. Checking install state..."

if [ -f "$MARKER" ]; then
    echo "[voice-autoinstall] Already installed — skipping."
    echo "[voice-autoinstall] Delete ~/.agentium/voice-installed.marker to force reinstall."
    exit 0
fi

mkdir -p /root/.agentium

# ── Detect Windows vs Unix ────────────────────────────────────────────────────
# Docker Desktop for Windows bind-mounts USERPROFILE as /host_home.
# The AppData directory is a reliable Windows-only marker.
IS_WINDOWS=false
if [ -d "/host_home/AppData" ]; then
    IS_WINDOWS=true
fi

# ─────────────────────────────────────────────────────────────────────────────
# WINDOWS PATH
# ─────────────────────────────────────────────────────────────────────────────
if [ "$IS_WINDOWS" = "true" ]; then
    echo "[voice-autoinstall] Windows host detected."

    # ── Resolve the real Windows repo root ───────────────────────────────────
    # Docker Desktop exposes mount sources as:
    #   /run/desktop/mnt/host/c/Users/Alice/repos/agentium/scripts
    # We strip the Docker Desktop prefix and convert to a Windows path.
    SCRIPTS_SRC=$(awk '$2=="/scripts"{print $1}' /proc/mounts 2>/dev/null | head -1 || true)
    WIN_REPO=""

    if echo "$SCRIPTS_SRC" | grep -qE "^/run/desktop/mnt/host/"; then
        # Strip prefix, drop trailing /scripts component, convert to Windows path
        # e.g.  /run/desktop/mnt/host/c/Users/Alice/repos/agentium/scripts
        #    →  c\Users\Alice\repos\agentium
        #    →  C:\Users\Alice\repos\agentium
        UNIX_REPO=$(echo "$SCRIPTS_SRC" | sed 's|/run/desktop/mnt/host/||; s|/scripts$||')
        DRIVE=$(echo "$UNIX_REPO" | cut -d/ -f1 | tr '[:lower:]' '[:upper:]')
        REST=$(echo "$UNIX_REPO" | cut -d/ -f2- | tr '/' '\\')
        WIN_REPO="${DRIVE}:\\${REST}"
    elif echo "$SCRIPTS_SRC" | grep -qE "^/host_mnt/"; then
        UNIX_REPO=$(echo "$SCRIPTS_SRC" | sed 's|/host_mnt/||; s|/scripts$||')
        DRIVE=$(echo "$UNIX_REPO" | cut -d/ -f1 | tr '[:lower:]' '[:upper:]')
        REST=$(echo "$UNIX_REPO" | cut -d/ -f2- | tr '/' '\\')
        WIN_REPO="${DRIVE}:\\${REST}"
    fi

    if [ -z "$WIN_REPO" ]; then
        echo "[voice-autoinstall] WARN: Could not auto-detect repo root from mount source."
        echo "[voice-autoinstall] Falling back to %USERPROFILE%\\agentium"
        WIN_REPO='%USERPROFILE%\agentium'
    fi

    echo "[voice-autoinstall] Resolved Windows repo root: $WIN_REPO"

    # ── 1. Write bootstrap-voice.cmd ─────────────────────────────────────────
    # Source template is in scripts/windows-bootstrap.cmd (mounted read-only).
    # We copy it to /root/.agentium (which maps to %USERPROFILE%\.agentium)
    # and bake in the real repo root.
    BOOTSTRAP_TEMPLATE="/scripts/windows-bootstrap.cmd"
    BOOTSTRAP_DEST="/root/.agentium/bootstrap-voice.cmd"

    if [ -f "$BOOTSTRAP_TEMPLATE" ]; then
        sed "s|AGENTIUM_REPO_ROOT|${WIN_REPO}|g" "$BOOTSTRAP_TEMPLATE" > "$BOOTSTRAP_DEST"
        echo "[voice-autoinstall] bootstrap-voice.cmd written to %USERPROFILE%\\.agentium\\"
    else
        echo "[voice-autoinstall] WARN: windows-bootstrap.cmd not found in /scripts — writing inline fallback"
        cat > "$BOOTSTRAP_DEST" << CMDEOF
@echo off
setlocal
set LOG=%USERPROFILE%\.agentium\bootstrap.log
echo [%DATE% %TIME%] Bootstrap started >> "%LOG%"
set SETUP=${WIN_REPO}\voice-bridge\setup.ps1
powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%SETUP%" >> "%LOG%" 2>&1
echo [%DATE% %TIME%] Done >> "%LOG%"
CMDEOF
    fi

    # ── 2. Write Startup folder stub ─────────────────────────────────────────
    STARTUP_DIR="/host_home/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"
    STARTUP_STUB="$STARTUP_DIR/agentium-voice-startup.cmd"

    if [ -d "$STARTUP_DIR" ]; then
        STUB_TEMPLATE="/scripts/agentium-voice-startup.cmd"
        if [ -f "$STUB_TEMPLATE" ]; then
            cp "$STUB_TEMPLATE" "$STARTUP_STUB"
        else
            # Inline fallback
            printf '@echo off\r\nstart "" /min cmd /c "%%USERPROFILE%%\\.agentium\\bootstrap-voice.cmd"\r\n' > "$STARTUP_STUB"
        fi
        echo "[voice-autoinstall] Login startup stub written to Windows Startup folder."
    else
        echo "[voice-autoinstall] WARN: Could not find Windows Startup folder at:"
        echo "[voice-autoinstall]   $STARTUP_DIR"
        echo "[voice-autoinstall] The bridge will NOT auto-start on login."
    fi

    echo ""
    echo "[voice-autoinstall] ✅ Windows setup complete."
    echo "[voice-autoinstall]    The voice bridge will start automatically on your next Windows login."
    echo "[voice-autoinstall]    To start it RIGHT NOW (no reboot needed), open PowerShell and run:"
    echo "[voice-autoinstall]      powershell -ExecutionPolicy Bypass -File \"${WIN_REPO}\\voice-bridge\\setup.ps1\""

# ─────────────────────────────────────────────────────────────────────────────
# UNIX PATH  (Linux / macOS / WSL2)
# ─────────────────────────────────────────────────────────────────────────────
else
    echo "[voice-autoinstall] Unix host detected."

    apt-get update -qq > /dev/null 2>&1
    apt-get install -y -qq bash curl python3 python3-venv python3-pip > /dev/null 2>&1

    echo "[voice-autoinstall] Running OS detection..."
    bash /scripts/detect-host.sh

    echo "[voice-autoinstall] Installing voice bridge..."
    bash /scripts/install-voice-bridge.sh

    echo "[voice-autoinstall] ✅ Voice bridge installed and running."
fi

touch "$MARKER"
echo "[voice-autoinstall] Done. Log: ~/.agentium/install.log"