@echo off
chcp 65001 >nul
cd /d "%~dp0\..\.."
python -X utf8 scripts\post_builder.py serve "20261110-bianliangzhishu" --open
if errorlevel 1 pause
