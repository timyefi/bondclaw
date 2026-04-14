@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   BondClaw CLI Tools Setup
echo   Installing Node.js + npm + Claude Code
echo ========================================
echo.

:: Determine resources directory (this script lives in resources/)
set "RES_DIR=%~dp0"

:: Paths
set "NODE_EXE=%RES_DIR%bundled-node\win32-x64\node.exe"
set "INSTALL_SCRIPT=%RES_DIR%install-cli-tools.cjs"

:: Check bundled Node.js
if not exist "%NODE_EXE%" (
    echo [ERROR] Bundled Node.js runtime not found:
    echo         %NODE_EXE%
    echo.
    echo Make sure this script is in the resources folder of BondClaw.
    goto :fail
)

:: Check install script
if not exist "%INSTALL_SCRIPT%" (
    echo [ERROR] Install script not found:
    echo         %INSTALL_SCRIPT%
    goto :fail
)

echo [1/2] Deploying Node.js runtime and Claude Code...
echo       Target: %LOCALAPPDATA%\BondClaw\cli\
echo.
"%NODE_EXE%" "%INSTALL_SCRIPT%"
if !ERRORLEVEL! neq 0 (
    echo.
    echo [FAIL] Install script failed with exit code !ERRORLEVEL!
    goto :fail
)

echo.
echo [2/2] Verifying installation...
"%LOCALAPPDATA%\BondClaw\cli\bin\node.cmd" --version 2>nul
if !ERRORLEVEL! neq 0 (
    echo [WARN] node verification failed, but install script completed.
)

echo.
echo ========================================
echo   Setup complete!
echo.
echo   Please:
echo   - Close and reopen your terminal
echo   - Then run: node / npm / claude
echo ========================================
echo.
pause
exit /b 0

:fail
echo.
echo ========================================
echo   Setup failed.
echo.
echo   You can also click the "One-Click Install"
echo   button inside the BondClaw app.
echo ========================================
echo.
pause
exit /b 1
