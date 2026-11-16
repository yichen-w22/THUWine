@echo off
chcp 65001 >nul
cd /d "%~dp0\..\.."
python -X utf8 scripts\post_builder.py stop "20261024-lewei"
if errorlevel 1 pause
