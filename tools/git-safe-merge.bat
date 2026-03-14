@echo off
:: Copy the script to temp so it survives git checkout (which may delete repo files)
copy /Y "%~dp0git-safe-merge.ps1" "%TEMP%\git-safe-merge.ps1" >nul
powershell -ExecutionPolicy Bypass -File "%TEMP%\git-safe-merge.ps1" -WorkingDir "%~dp0"
pause
