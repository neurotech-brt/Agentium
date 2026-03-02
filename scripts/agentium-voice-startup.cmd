@echo off
:: Agentium Voice Bridge — auto-start on Windows login
:: Placed in Startup folder by docker-compose voice-autoinstall service.
start "" /min cmd /c "%USERPROFILE%\.agentium\bootstrap-voice.cmd"