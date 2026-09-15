@echo off
chcp 65001 >nul
"%~dp0python\python.exe" "%~dp0scripts\apply_localization.py"
if errorlevel 1 (
    echo.
    echo ============================================================
    echo  The Python runtime itself failed to start ^(exit code %errorlevel%^),
    echo  before the toolkit's own error handling could even run.
    echo  This usually means the vendored python\ folder is broken or
    echo  incomplete ^(e.g. missing python310.zip^) -- send this window
    echo  to whoever maintains the toolkit.
    echo ============================================================
    echo.
    pause
)
