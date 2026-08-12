@echo off
setlocal
rem ==========================================================
rem  RULES FOR THIS FILE. See the same header in the view .bat
rem  - both files are one paired surface.
rem
rem  RULE 1 - ASCII ONLY. No Chinese characters anywhere.
rem    Under "chcp 65001" the cmd.exe batch parser tracks its read
rem    position in BYTES, so multi-byte UTF-8 characters make it
rem    resume mid-line. Chinese UI text lives in SETUP.md.
rem    NOTE - 65001 is NOT optional here: every research folder in this
rem    project has a Chinese name, so git's own output is UTF-8.
rem    Choosing CP950 to allow Chinese echo text would mojibake the
rem    file paths - which is the part the user actually needs to read.
rem
rem  RULE 2 - NEVER "set VAR" then read "%VAR%" inside the SAME
rem           ( ) block. cmd expands the whole block at PARSE time.
rem    This file uses flat goto flow so the pattern cannot occur.
rem
rem  RULE 3 - FOLDER IDENTITY MUST BE PROVEN BEFORE ANY WRITE.
rem    Two guards, both required, both ASCII-safe:
rem      a) sentinel files AGENTS.md + Research_Charter.md must exist
rem      b) "git rev-parse --show-prefix" must be EMPTY
rem    Guard (b) catches the case where THIS folder is not a repo but
rem    a PARENT folder is - then "git add -A" would stage the parent's
rem    entire tree. This exact bug was hit in this project on
rem    2026-08-07 by a sensor using "git -C", which silently reported
rem    16 violations against the wrong repository.
rem    Guard (b) compares against "" so it never parses a Chinese path.
rem
rem  RULE 4 - EVERY STATE THAT PRODUCES NO OUTPUT MUST SAY SO,
rem           AND WHAT IT SAYS MUST BE TRUE.
rem    A blank section is ambiguous between "nothing changed" and
rem    "the command failed". Where a blank has SEVERAL causes, each
rem    must be distinguished and named; one cause must not stand in
rem    for all of them. Saying something is not saying something true.
rem
rem  RULE 5 - EVERY GIT COMMAND THAT PRINTS A PATH MUST GO THROUGH
rem           %GITQ%, NOT bare "git".
rem    Git escapes non-ASCII path bytes by default, so a Chinese folder
rem    name prints as "\345\205\266\344\273\226..." instead of text.
rem    EVERY research folder in this project has a Chinese name, so the
rem    default turns the single most important column - which file
rem    changed - into unreadable octal.
rem    Observed 2026-08-08 on the very first real run of these files.
rem    The identical bug had already been found and fixed in
rem    sensor_scope_and_t0.py on 2026-08-07; it was simply not carried
rem    over here. A named variable is used instead of repeating the
rem    flag so that a missing one is visible rather than silent.
rem    Enforced by scripts/harness/selftest_bat.py :: QUOTEPATH_MISSING
rem ==========================================================
chcp 65001 >nul
cd /d "%~dp0"
set GITQ=git -c core.quotepath=false
set LOG=git-snapshot.log
set MODE=%~1
set LABEL=%~2
if "%LABEL%"=="" set LABEL=unlabelled

echo ============================================
if /i "%MODE%"=="auto" echo   SNAPSHOT [AI auto checkpoint]
if /i not "%MODE%"=="auto" echo   SNAPSHOT [human review point]
echo ============================================
echo.
echo [%date% %time%] ---- start mode=%MODE% ---- > "%LOG%"

rem ---- GUARD 3a: is this the right folder at all? ----
rem Sentinel files prove this is the project folder. Change these two
rem names if you rename the governance files - but do NOT remove the check.
if not exist "governance\AGENTS.md" goto :wrong_folder
if not exist "governance\WORKFLOW_CONSTITUTION.md" goto :wrong_folder

where git >nul 2>nul
if errorlevel 1 goto :no_git
git --version >> "%LOG%" 2>&1

rem ---- clear stale locks BEFORE rev-parse, so the guard can run ----
rem Git uses MANY lock files, not three. Enumerating them by name is
rem what failed on 2026-08-08: a commit aborted on
rem   .git/refs/heads/master.lock
rem which this file did not clear and did not even check for, so it
rem reported only "git commit failed" with no usable cause.
rem The staged work was intact, but the message gave no way to know that.
rem Sweep the whole tree instead of listing names. A stale lock on a
rem single-user desktop is far more likely than a genuine concurrent
rem git process; the trade-off is stated in SETUP.md section 3.
for /r ".git" %%f in (*.lock) do del /f /q "%%f" >nul 2>&1
if exist ".git\index.lock" goto :lock_stuck
if exist ".git\refs\heads\master.lock" goto :lock_stuck

rem ---- GUARD 3b: repo exists, and its root is HERE ----
git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto :init_repo
rem findstr returns 0 only if the prefix has at least one character,
rem i.e. only if we are in a SUBDIRECTORY of some other repository.
git rev-parse --show-prefix 2>nul | findstr /r /c:"." >nul
if not errorlevel 1 goto :wrong_repo
goto :repo_ok

:init_repo
echo No repository here yet - creating one.
echo [%date% %time%] git init >> "%LOG%"
git init >> "%LOG%" 2>&1
if errorlevel 1 goto :init_failed
echo Done. This folder is now tracked.
echo.

:repo_ok
if not exist ".gitignore" echo [WARNING] .gitignore is missing - large scratch files may be committed.

echo Changes since the last checkpoint:
echo --------------------------------------------
%GITQ% --no-pager diff --stat --summary HEAD 2>> "%LOG%"
%GITQ% ls-files --others --exclude-standard 2>> "%LOG%"
echo --------------------------------------------
echo.

echo Working - the first run can take a while on a large folder.
git add -A >> "%LOG%" 2>&1
if errorlevel 1 goto :add_failed

rem "nothing to commit" must NOT skip the reviewed-tag step. In human
rem mode the point of this script is to record "I have seen everything
rem up to here" - which is still meaningful, and usually the WHOLE
rem point, when the AI has already committed the work itself.
git diff --cached --quiet 2>> "%LOG%"
if not errorlevel 1 goto :nothing_to_commit

set STAMP=
for /f "tokens=*" %%i in ('powershell -NoProfile -Command "Get-Date -Format \"yyyy-MM-dd HH:mm\""') do set STAMP=%%i
if "%STAMP%"=="" set STAMP=no-timestamp
if /i "%MODE%"=="auto" goto :commit_auto

git commit -m "snapshot %STAMP%" >> "%LOG%" 2>&1
if errorlevel 1 goto :commit_failed
goto :committed

:commit_auto
git commit -m "auto: %STAMP% [%LABEL%] -- AI auto checkpoint, NOT human-reviewed" >> "%LOG%" 2>&1
if errorlevel 1 goto :commit_failed

:committed
echo New checkpoint created.
goto :review_tag

:nothing_to_commit
echo No uncommitted changes - no new checkpoint needed.
echo [%date% %time%] nothing-to-commit >> "%LOG%"

:review_tag
if /i "%MODE%"=="auto" goto :auto_no_tag
git rev-parse --verify reviewed >nul 2>&1
if errorlevel 1 goto :first_tag
echo.
echo Checkpoints you are marking as reviewed:
echo --------------------------------------------
git --no-pager log --oneline reviewed..HEAD 2>> "%LOG%"
git --no-pager log --oneline reviewed..HEAD >> "%LOG%" 2>&1
echo --------------------------------------------
:first_tag
git tag -f reviewed >> "%LOG%" 2>&1
if errorlevel 1 goto :tag_failed
echo Done. Reviewed baseline moved to the latest checkpoint.
goto :show_log

:auto_no_tag
echo Done. Auto checkpoint - reviewed baseline NOT moved.

:show_log
echo.
echo Latest checkpoints:
echo --------------------------------------------
git --no-pager log --oneline -5 2>> "%LOG%"
echo --------------------------------------------
git --no-pager log --oneline -5 >> "%LOG%" 2>&1
echo [%date% %time%] ---- end rc=0 ---- >> "%LOG%"
echo.
echo NEXT: see NEXT_SESSION_MEMO.md for this round's task.
echo.
call :hold
exit /b 0

:wrong_folder
echo [ERROR] This is not the research project folder.
echo governance/AGENTS.md was not found under this folder.
echo Nothing was written. Move this .bat back into the project folder.
echo [%date% %time%] wrong folder >> "%LOG%"
call :hold
exit /b 1

:wrong_repo
echo [ERROR] This folder is INSIDE another Git repository.
echo Committing here would stage that other repository's files.
echo Nothing was written. Send %LOG% to Claude.
echo [%date% %time%] repo root mismatch >> "%LOG%"
call :hold
exit /b 1

:no_git
echo [ERROR] Git not found.
echo Install from https://git-scm.com/download/win
echo [%date% %time%] git missing >> "%LOG%"
call :hold
exit /b 1

:init_failed
echo [ERROR] git init failed - see %LOG%
echo [%date% %time%] git init failed >> "%LOG%"
call :hold
exit /b 1

:lock_stuck
echo [ERROR] A Git lock file could not be removed - another program
echo may have this folder open, or a git process is still running.
echo Close any editor or sync tool using this folder, then try again.
echo [%date% %time%] lock delete failed >> "%LOG%"
call :hold
exit /b 1

:add_failed
echo [ERROR] git add failed - see %LOG%
echo [%date% %time%] git add failed >> "%LOG%"
call :hold
exit /b 1

:commit_failed
echo [ERROR] git commit failed. Send %LOG% to Claude.
echo [%date% %time%] ---- end COMMIT-FAILED ---- >> "%LOG%"
call :hold
exit /b 1

:tag_failed
echo [ERROR] git tag -f reviewed failed. Send %LOG% to Claude.
echo [%date% %time%] ---- end TAG-FAILED ---- >> "%LOG%"
call :hold
exit /b 1

rem ---- Hold the window open for a human, but NEVER for an
rem      automated caller. "pause" waits for a keypress forever;
rem      if the AI invokes this file in auto mode that is a hang,
rem      not a prompt. Both branches are flat statements, so
rem      RULE 2 cannot apply.
:hold
if /i "%MODE%"=="auto" timeout /t 3 >nul 2>&1
if /i not "%MODE%"=="auto" pause
goto :eof
