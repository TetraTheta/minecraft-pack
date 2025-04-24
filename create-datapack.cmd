@echo off
setlocal

@REM Find and use '7za.exe' in PATH
where 7za.exe >nul 2>&1
if %ErrorLevel% equ 0 (
  set "sevenzip=7za.exe"
) else (
  set "sevenzip=C:\Program Files\7-Zip-Zstandard\7za.exe"
)

"%sevenzip%" a -tzip -mx9 "%~dp0\custom-datapack.zip" -xr@"%~dp0\exclude-data-pack.txt" "%~dp0\data-pack\*"

endlocal
pause
