@echo off
setlocal

REM Build a Windows DLL using MinGW-w64 gcc
REM Output: task_manager.dll

gcc -O2 -shared -o task_manager.dll task_manager.c

if %errorlevel% neq 0 (
  echo Build failed.
  exit /b %errorlevel%
)

echo Built task_manager.dll successfully.
endlocal