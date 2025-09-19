@echo off

if "%1" == "" goto InvalidArgs
if not exist "%1\" goto InvalidArgs
goto Normal

:InvalidArgs
echo "Usage: intg-test <path>"
exit 1

:Normal
set "testClassFolder=%~dp0"
set "compiler=%testClassFolder%..\toolkit\tools\JackCompiler.bat"
set "emulator=%testClassFolder%..\toolkit\tools\VMEmulator.bat"

pushd %1
SETLOCAL ENABLEDELAYEDEXPANSION

for %%f in ("%testClassFolder%*.jack") do (
    set "testClass=%%~nf"
    if exist "!testClass!.jack" del "!testClass!.jack"
    if exist "!testClass!.vm" del "!testClass!.vm"
    copy "%%f" "%%~nxf"
)

cmd /c "%compiler%" .
tasklist | findstr "javaw"
if %ERRORLEVEL% NEQ 0 "%emulator%"

ENDLOCAL
popd