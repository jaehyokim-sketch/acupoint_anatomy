@echo off
chcp 65001 > nul
echo ========================================================
echo   acupoint_anatomy Local -> Google Drive Deployer
echo ========================================================
python -u "%~dp0deploy_to_gdrive.py"
pause
