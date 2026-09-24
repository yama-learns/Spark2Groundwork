@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0" || exit /b 2
if not "%~2"=="" exit /b 2
if not "%~1"=="" if /i not "%~1"=="--no-pause" exit /b 2
set "PY="
rem Prefer installed runtimes, not Store aliases or auto-install launchers.
for /d %%D in ("%LOCALAPPDATA%\Python\pythoncore-*") do call :probe "%%~D\python.exe"
for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python*") do call :probe "%%~D\python.exe"
for /d %%D in ("%ProgramFiles%\Python*") do call :probe "%%~D\python.exe"
for /f "delims=" %%P in ('where python.exe 2^>nul') do call :probe "%%P"
for /f "delims=" %%P in ('where python3.exe 2^>nul') do call :probe "%%P"
if not defined PY goto :missing
"%PY%" -I -B "%~dp0scripts\harness\check_environment.py" --lang zh --action reviewed
set "RC=%ERRORLEVEL%"
goto :done
:missing
echo [INCOMPLETE] Python 3.9+ was not found. Opening the local setup guide.
start "" "%~dp0docs\START_HERE.html"
set "RC=2"
:done
echo.
echo RESULT CODE: %RC%  ^(0=PASS, 1=FAIL, 2=INCOMPLETE^)
if /i not "%~1"=="--no-pause" pause
exit /b %RC%
:probe
if defined PY exit /b 0
if not exist "%~1" exit /b 0
set "CANDIDATE=%~1"
rem Skip Microsoft Store alias stubs: no browser or installer side effect.
if not "%CANDIDATE:WindowsApps=%"=="%CANDIDATE%" exit /b 0
"%~1" -I -B -c "import sys;sys.exit(0 if sys.version_info >= (3,9) else 2)" >nul 2>nul
if not errorlevel 1 set "PY=%~1"
exit /b 0
