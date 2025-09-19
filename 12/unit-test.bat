@echo off

if "%1" == "" goto InvalidArgs
if not exist "%1\" goto InvalidArgs
goto Normal

:InvalidArgs
echo "Usage: unit-test <path>"
exit 1

:Normal
set "testClassFolder=%~dp0"
set "compiler=%testClassFolder%..\toolkit\tools\JackCompiler.bat"
set "emulator=%testClassFolder%..\toolkit\tools\VMEmulator.bat"

pushd %1
setlocal

for %%I in (.) do set "CurrentFolderName=%%~nxI"
set "testClass=%CurrentFolderName:Test=%"
set "testClass=%testClass:Diag=%"

if exist "%testClass%.jack" del "%testClass%.jack"
if exist "%testClass%.vm" del "%testClass%.vm"
copy "%testClassFolder%%testClass%.jack" "%testClass%.jack"

cmd /c "%compiler%" .
tasklist | findstr "javaw"
if %ERRORLEVEL% NEQ 0 "%emulator%"

endlocal
popd