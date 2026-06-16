@echo off
setlocal
set "ROOT=%~dp0"

echo ============================================
echo   NewsDigest - 智能新闻聚合工具
echo ============================================
echo.

echo [1/2] Starting backend...
start "NewsDigest Backend" cmd /k "cd /d ""%ROOT%backend"" && python -m pip install -r requirements.txt -q && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting frontend...
start "NewsDigest Frontend" cmd /k "cd /d ""%ROOT%frontend"" && npm install -q && npm run dev -- --host 0.0.0.0"

echo.
echo Backend:  http://localhost:8000
echo API docs: http://localhost:8000/docs
echo Frontend: http://localhost:5173
echo.
echo Open http://localhost:5173 in your browser.
pause
