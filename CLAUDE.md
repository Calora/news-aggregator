# NewsDigest 项目规则

## 项目性质

技术新闻聚合系统，Python FastAPI 后端 + React TypeScript 前端 + SQLite。

## 架构

```
前端 (React+Vite, :5173) → API → 后端 (FastAPI, :8000) → SQLite
                                      ↓
                               DeepSeek API (分类/评分/摘要)
```

## 数据模型

Article / DailyReport / EmailAccount / WebSource / FetchLog

## 常用命令

```bash
# 启动后端
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# 启动前端
cd frontend && npm run dev -- --host 0.0.0.0
# 健康检查
python health_check.py
```

## 绝对禁止操作（必须先确认）

1. **禁止删除数据库** — 绝对不能执行 `rm` / `delete` / `os.remove()` 删除 `news_aggregator.db`，也不能用 `taskkill` 杀掉数据库进程后再重建。任何涉及数据库清空的操作必须先向用户确认。
2. **禁止删除用户数据** — `is_bookmarked=1` 的文章（用户收藏）在任何数据库操作中都必须保留。
3. **禁止 `taskkill /F /IM python.exe`** — 这会杀掉所有 Python 进程，可能导致数据丢失。如需重启后端，只杀掉占用 8000 端口的特定 PID。
4. **禁止修改 `.env` 中的密钥和 EMAIL_ACCOUNTS** — 除非用户明确要求。

## 修改代码规则

1. 修改后端代码后，先 `python -c "from app.main import app; print('OK')"` 验证编译通过
2. 前端修改后，先 `npx tsc --noEmit` 检查类型
3. 重启后端前，确认用户已保存数据
4. 任何 `import` 路径的修改，要验证相对路径的层级（services 用 `..`，同级用 `.`）

## 数据库操作规则

1. 任何 UPDATE/DELETE 操作先在测试环境验证
2. 批量修改数据前告知用户影响范围
3. 保留 `is_bookmarked=1` 的文章不动
