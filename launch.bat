@echo off
rem Search for and kill any running Python processes
taskkill /F /IM python.exe

rem Start app.py in a minimized window
start /min /B python c:\Users\chris\CascadeProjects\smqt_practice\app.py

rem Wait a moment for the server to start
timeout /t 2 /nobreak > nul

rem Open the web browser to the specified URL
start "" "http://127.0.0.1:5000"
