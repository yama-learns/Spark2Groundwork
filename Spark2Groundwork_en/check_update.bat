@echo off
rem ===========================================================
rem  Framework upgrade: check / diff / apply
rem
rem  This file is a BUTTON, not the program. All the logic lives
rem  in scripts\harness\upgrade.py so that Windows and macOS run
rem  exactly the same code. Do not copy logic back into here:
rem  two copies of one thing is how this framework's own
rem  "fixed one layer, missed another" incidents happened.
rem ===========================================================
setlocal
rem UTF-8 console. The scripts already force UTF-8 output so they cannot
rem crash without this, but the console would render mojibake.
chcp 65001 >nul
cd /d "%~dp0"

set PY=
where python >nul 2>nul && set PY=python
if "%PY%"=="" (where py >nul 2>nul && set PY=py -3)
if "%PY%"=="" (where python3 >nul 2>nul && set PY=python3)
if "%PY%"=="" goto :no_python

if not "%~1"=="" goto :run_args
%PY% "scripts\harness\upgrade.py" check
set "RC=%ERRORLEVEL%"
if not exist "_upgrade\" goto :done
echo.
%PY% "scripts\harness\upgrade.py" diff
if not "%ERRORLEVEL%"=="0" set "RC=%ERRORLEVEL%"
goto :done

:run_args
%PY% "scripts\harness\upgrade.py" %*
set "RC=%ERRORLEVEL%"

:done
echo.
echo ===========================================================
pause
exit /b %RC%

:no_python
echo.
echo [FAIL] Python was not found on this computer.
echo.
echo   This framework needs Python 3.9 or newer.
echo   Download: https://www.python.org/downloads/
echo   IMPORTANT: tick "Add Python to PATH" during installation.
echo.
echo   Nothing was changed.
echo.
pause
exit /b 1
