@echo off
echo ============================================================
echo  Starting Tri-Agent Web Dashboard on http://localhost:8080
echo ============================================================
start "" "http://localhost:8080"
"C:\Users\Aryan\AppData\Local\Programs\Python\Python312\python.exe" server.py 8080
pause
