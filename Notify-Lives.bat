@echo off
chcp 65001 > nul
cd /d C:\Dev\Automacao_Lives
call .venv\Scripts\activate
python Notify-Lives-1.0.py
timeout 6