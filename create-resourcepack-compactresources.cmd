@echo off
setlocal

set "PATH=C:\Program Files\7-Zip-Zstandard;C:\Program Files\7-Zip;%PATH%"

7za.exe a -tzip -mx9 "%~dp0\compact-resources-pack.zip" -xr@"%~dp0\exclude-data-pack.txt" "%~dp0\resource-pack\compact-resources-pack\*"

endlocal
pause
