@echo off
cd /d "D:\video-organizer"
call venv\Scripts\activate
set FLASK_APP=app.py
set FLASK_DEBUG=1
start "" http://127.0.0.1:5000
flask run
pause