@echo off
cd /d "l:\posches 911 tuboS\crypto-bot"
set PYTHONIOENCODING=utf-8
python main.py --test >> bot.log 2>&1
