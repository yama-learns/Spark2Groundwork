@echo off
setlocal
rem ==========================================================
rem  RULES FOR THIS FILE. See the same header in the snapshot
rem  .bat - both files are one paired surface.
rem
rem  RULE 1 - ASCII ONLY. No Chinese characters anywhere.
rem    Under "chcp 65001" the cmd.exe batch parser tracks its read
rem    position in BYTES, so multi-byte UTF-8 characters make it
rem    resume mid-line. Chinese UI text lives in Git_Usage_Note.md.
rem    NOTE - 65001 is NOT optional here: every research folder in
rem    this project has a Chinese name, so git's own output is UTF-8.
rem    Choosing CP950 to allow Chinese echo text would mojibake the
rem    file paths - which is the part the user actually needs to read.
rem
rem  RULE 2 - NEVER "set VAR" then read "%VAR%" inside the SAME
rem           ( ) block. cmd expands the whole block at PARSE time.
rem    This file uses flat goto flow so the pattern cannot occur.
rem
rem  RULE 3 - READ-ONLY GIT COMMANDS ONLY. This file must never
rem    write to the repository: no add, commit, tag, stash, checkout,
rem    reset, and NO deleting of .git lock files.
rem    Measured 2026-07-31 with index.lock AND HEAD.lock both present:
rem      rev-parse / diff --stat / ls-files / log / diff -- <file>
rem      all returned exit 0 with complete output. A read-only tool
rem      gains nothing from deleting a lock, but deleting one can
rem      corrupt the index write of whatever process legitimately
rem      holds it. The snapshot .bat handles stale locks; this one
rem      does not touch them.
rem
rem  RULE 4 - EVERY STATE THAT PRODUCES NO OUTPUT MUST SAY SO.
rem    A blank section is ambiguous between "nothing changed" and
rem    "the command failed". On a fresh repository with no commits,
rem    "git diff HEAD" aborts with a fatal error; that state is
rem    handled explicitly at :no_commits rather than left to print
rem    a raw git error the reader cannot interpret.
rem    This mirrors the project-wide rule that INCOMPLETE is not PASS.
rem    EXTENDED 2026-08-08 after the second live run: when a blank
rem    output has SEVERAL possible causes, each must be distinguished
rem    and named. Do not let one cause stand in for all of them.
rem    Observed: a dragged file that Git had never seen was reported
rem    as "unchanged" - which is not vague, it is false. The same
rem    screen also listed it as new, so the tool contradicted itself.
rem    Saying something is not the same as saying something true.
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
set MODE=
if /i "%~1"=="auto" set MODE=auto
set LOG=git-view.log
echo [%date% %time%] ---- start ---- > "%LOG%"

echo ============================================
echo   WHAT CHANGED since your last reviewed point
echo ============================================
echo.

rem Sentinel files prove this is the project folder. Change these two
rem names if you rename the governance files - but do NOT remove the check.
if not exist "governance\AGENTS.md" goto :wrong_folder
if not exist "governance\WORKFLOW_CONSTITUTION.md" goto :wrong_folder

where git >nul 2>nul
if errorlevel 1 goto :no_git

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto :no_repo
git rev-parse --show-prefix 2>nul | findstr /r /c:"." >nul
if not errorlevel 1 goto :wrong_repo

git rev-parse --verify HEAD >nul 2>&1
if errorlevel 1 goto :no_commits

set BASE=HEAD
git rev-parse --verify reviewed >nul 2>&1
if not errorlevel 1 set BASE=reviewed

echo Comparing against: %BASE%
if "%BASE%"=="HEAD" echo [No reviewed baseline yet - run the snapshot .bat once to create it]
echo.
echo [1] Files touched, and how many lines
echo --------------------------------------------
%GITQ% --no-pager diff --stat --summary %BASE% 2>> "%LOG%"
echo --------------------------------------------
echo [If section 1 is blank: no tracked file differs from %BASE%]
echo.
echo [2] New files not yet under version control
echo --------------------------------------------
%GITQ% ls-files --others --exclude-standard 2>> "%LOG%"
echo --------------------------------------------
echo [If section 2 is blank: no new files]
echo.
echo [3] Checkpoints since your last reviewed point
echo     [lines starting with "auto:" are AI checkpoints, NOT human-reviewed]
echo --------------------------------------------
git --no-pager log --oneline %BASE%..HEAD 2>> "%LOG%"
echo --------------------------------------------
echo [If section 3 is blank: no new checkpoints since you last reviewed]
echo.

if "%~1"=="" goto :no_file_arg
if /i "%~1"=="auto" goto :no_file_arg
echo [4] Line-by-line diff for: %~1
echo --------------------------------------------
rem A blank diff has THREE different causes and they are not
rem interchangeable. Saying "unchanged" for a file Git has never
rem seen is a false statement, not a vague one - so each case is
rem tested and named before the diff is printed. See RULE 4.
git check-ignore -q "%~1" 2>nul
if not errorlevel 1 goto :file_ignored
%GITQ% ls-files --error-unmatch "%~1" >nul 2>&1
if errorlevel 1 goto :file_untracked
%GITQ% --no-pager diff %BASE% -- "%~1" 2>> "%LOG%"
echo --------------------------------------------
echo [If section 4 is blank: that file is unchanged since %BASE%]
echo.
goto :done

:file_untracked
echo This file is NOT tracked by Git yet, so there is nothing to
echo compare it against. It appears in section [2] above as new.
echo It will be tracked after you run the snapshot .bat.
echo --------------------------------------------
echo.
goto :done

:file_ignored
echo This file is deliberately EXCLUDED from tracking by .gitignore
echo - see Git_Usage_Note.md section 5 for which files and why.
echo Nothing is recorded about it, so no comparison is possible.
echo --------------------------------------------
echo.
goto :done

:no_file_arg
echo TIP: to see one file line-by-line, DRAG that file onto this .bat icon.
echo.

:done
echo [%date% %time%] ---- end ---- >> "%LOG%"
call :hold
exit /b 0

:no_commits
echo This repository has no checkpoints yet - there is nothing to compare against.
echo Run the snapshot .bat once to create the first one.
echo [%date% %time%] no commits >> "%LOG%"
call :hold
exit /b 0

:wrong_folder
echo [ERROR] This is not the research project folder.
echo governance/AGENTS.md was not found under this folder.
echo Move this .bat back into the project folder.
echo [%date% %time%] wrong folder >> "%LOG%"
call :hold
exit /b 1

:no_repo
echo This folder is not tracked by Git yet.
echo Run the snapshot .bat once to start tracking it.
echo [%date% %time%] no repo >> "%LOG%"
call :hold
exit /b 0

:wrong_repo
echo [ERROR] This folder is INSIDE another Git repository.
echo Any comparison shown would be against the wrong repository.
echo Send %LOG% to Claude.
echo [%date% %time%] repo root mismatch >> "%LOG%"
call :hold
exit /b 1

:no_git
echo [ERROR] Git not found. Install from https://git-scm.com/download/win
echo [%date% %time%] git missing >> "%LOG%"
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
