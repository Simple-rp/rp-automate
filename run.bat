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

set "NEED_INSTALL=0"
set "INSTALL_REASON="
set "CURRENT_REQ_HASH="
set "INSTALLED_REQ_HASH="

if exist "%REQ_FILE%" (
    for /f "usebackq delims=" %%H in (`!PY_CMD! -c "import hashlib, pathlib, os; p=pathlib.Path(os.environ['REQ_FILE']); print(hashlib.sha256(p.read_bytes()).hexdigest())" 2^>nul`) do (
        set "CURRENT_REQ_HASH=%%H"
    )

    if not defined CURRENT_REQ_HASH (
        set "NEED_INSTALL=1"
        set "INSTALL_REASON=could not read requirements hash"
    ) else (
        if not exist "%DEPS_MARKER%" (
            set "NEED_INSTALL=1"
            set "INSTALL_REASON=first launch"
        ) else (
            for /f "tokens=2 delims==" %%H in ('findstr /b /c:"sha256=" "%DEPS_MARKER%" 2^>nul') do (
                set "INSTALLED_REQ_HASH=%%H"
            )
            if /i not "!CURRENT_REQ_HASH!"=="!INSTALLED_REQ_HASH!" (
                set "NEED_INSTALL=1"
                set "INSTALL_REASON=requirements changed"
            )
        )
    )
)

if "%NEED_INSTALL%"=="1" (
    echo Installing Python dependencies from requirements.txt ^(!INSTALL_REASON!^)...
    call !PY_CMD! -m pip install -r "%REQ_FILE%"
    if errorlevel 1 (
        echo.
        echo Failed to install dependencies.
        pause
        goto end
    )
    (
        echo sha256=!CURRENT_REQ_HASH!
        echo installed_on=%DATE% %TIME%
    ) > "%DEPS_MARKER%"
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
