# Start Backend Server
cd $PSScriptRoot
.\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 5000 --reload

