@echo off
@setlocal
for %%A in ("%~dp0.") do set "parent=%%~dpA"
pushd "%parent%"
"C:\Program Files\7-Zip\7z.exe" a -tzip -mx9 -r -x!*.md "custom-datapack.zip" "data\*" "pack.mcmeta"
