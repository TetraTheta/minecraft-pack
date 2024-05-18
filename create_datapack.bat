@echo off
"C:\Program Files\7-Zip\7z.exe" a -tzip -mx9 -r -x!*.md "custom-datapack.zip" "data\*" "pack.mcmeta"
