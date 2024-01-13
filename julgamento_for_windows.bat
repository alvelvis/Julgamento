@ECHO OFF
if exist Python39\ (
    Python39\Python.exe for_windows.py
) else (
    echo There are missing files in this Windows release of Julgamento.
    echo 1. Please download the Windows release from https://github.com/alvelvis/Julgamento/releases
    echo 2. Make sure to open Julgamento from the file julgamento_for_windows only after extracting the zipped downloaded file Julgamento.zip to a folder of your choice.
)
pause
