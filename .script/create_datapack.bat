@echo off
@setlocal
for %%A in ("%~dp0.") do set "parent=%%~dpA"
pushd "%parent%"
"C:\Program Files\7-Zip\7z.exe" a -tzip -mx=9 "custom-datapack.zip" "data\*" "pack.mcmeta"
