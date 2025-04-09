@echo off
set "z=C:\Program Files\7-Zip-Zstandard\7z.exe"
"%z%" a -tzip -mx9 "custom-datapack.zip" -xr@"%~dp0\exclude.txt"
pause
