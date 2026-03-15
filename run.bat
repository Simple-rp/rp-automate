@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"

set "REQ_FILE=%CD%\requirements.txt"
set "DEPS_MARKER=%CD%\.deps_installed"

set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py -3"
if not defined PY_CMD (
    where python >nul 2>&1 && set "PY_CMD=python"
)

if not defined PY_CMD (
    echo Python not found in PATH.
    echo Install Python or add it to PATH.
    pause
    goto end
)

if exist "%REQ_FILE%" if not exist "%DEPS_MARKER%" (
    echo Installing Python dependencies from requirements.txt...
    call !PY_CMD! -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo.
        echo Failed to install dependencies.
        pause
        goto end
    )
    >"%DEPS_MARKER%" echo Installed on %DATE% %TIME%
)

:menu
cls
echo === FiveM Bot Launcher (.bat) ===
echo.

set /a count=0

for /r "scripts" %%F in (*.py) do (
    if /i not "%%~nxF"=="__init__.py" (
        set /a count+=1
        set "script[!count!]=%%~fF"
        set "display=%%~fF"
        set "display=!display:%CD%\scripts\=!"
        set "display=!display:\=/!"
        echo !count!. !display!
    )
)

echo.
if !count! EQU 0 (
    echo No Python scripts found in scripts\
)
echo [r] refresh
echo [0] quit
echo.
set "choice="
set /p "choice=Choice: "

if /i "%choice%"=="0" goto end
if /i "%choice%"=="q" goto end
if /i "%choice%"=="quit" goto end
if /i "%choice%"=="exit" goto end
if /i "%choice%"=="r" goto menu
if "%choice%"=="" goto menu

set "bad="
for /f "delims=0123456789" %%A in ("%choice%") do set "bad=1"
if defined bad goto invalid

set /a idx=%choice% 2>nul
if !idx! LSS 1 goto invalid
if !idx! GTR !count! goto invalid

set "target=!script[%idx%]!"
echo.
echo Running: !target!
echo.

call !PY_CMD! "!target!"
echo.
pause
goto menu

:invalid
echo.
echo Invalid choice.
timeout /t 1 >nul
goto menu

:end
echo Bye.
endlocal
