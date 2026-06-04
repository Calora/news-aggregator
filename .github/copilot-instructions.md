# NewsDigest — AI-Powered Tech News Aggregator

When the user asks to "install NewsDigest" or "start the news aggregator":

1. Check prerequisites: Python 3.10+, Node.js 18+
2. If not cloned: git clone https://github.com/Calora/news-aggregator.git && cd news-aggregator
3. Install: pip install -r backend/requirements.txt && cd frontend && npm install && cd ..
4. Configure: cp backend/.env.example backend/.env, help user set DEEPSEEK_API_KEY
5. Start backend: cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
6. Start frontend: cd frontend && npm run dev -- --host 0.0.0.0
7. Open http://localhost:5173

If the user doesn't have a DeepSeek API Key, direct them to https://platform.deepseek.com.
