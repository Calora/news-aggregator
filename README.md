# NewsDigest — AI 驱动的技术新闻聚合器

面向区块链、AI、密码学技术研究者的个性化新闻聚合工具。自动抓取多源信息，用大模型做分类、评分、中文摘要，每日生成精选日报。

## 特性

- **多源聚合**：RSS、网页抓取、邮件（Gmail API / IMAP）三条数据通道
- **AI 分类**：基于 DeepSeek 做三维分类（领域 × 技术标签 × 内容载体）+ 智能评分
- **每日日报**：早 8 点自动生成当日精选（≤10 条），侧栏日期归档
- **噪音过滤**：自动剔除行情/投机/灌水内容
- **我的收藏**：收藏感兴趣的文章，支持局域网多人使用
- **自动去重**：URL + 标题相似度双重去重

## 技术栈

| 层 | 技术 |
|----|------|
| 后端 | Python · FastAPI · APScheduler · SQLite |
| 前端 | React · TypeScript · Tailwind CSS · Vite |
| AI | DeepSeek API（OpenAI 兼容接口） |

## 项目结构

```
news-aggregator/
├── start.bat              # Windows 一键启动
├── health_check.py        # 外部健康巡检
├── backend/
│   ├── .env.example       # 配置模板
│   ├── app/
│   │   ├── main.py        # FastAPI 入口
│   │   ├── models.py      # 数据模型（5张表）
│   │   ├── routers/       # API 路由
│   │   └── services/      # 核心业务逻辑
│   │       ├── web_fetcher.py    # RSS / 网页抓取
│   │       ├── email_fetcher.py  # IMAP 邮件拉取
│   │       ├── gmail_fetcher.py  # Gmail API 邮件拉取
│   │       ├── classifier.py     # AI 分类 + 评分 + 摘要
│   │       ├── deduplicator.py   # URL + 标题去重
│   │       └── pipeline.py       # 完整流水线
│   └── scheduler.py       # 定时任务（每4小时抓取 + 每日8点生成日报）
└── frontend/
    └── src/
        ├── pages/          # 页面组件
        │   ├── DailyReportPage.tsx  # 日报页
        │   ├── AllNewsPage.tsx      # 全部动态
        │   ├── SourcesPage.tsx      # 数据源管理
        │   └── BookmarksPage.tsx    # 我的收藏
        └── components/     # UI 组件
```

## 快速开始

### 前置条件

- Python 3.10+
- Node.js 18+
- DeepSeek API Key（[platform.deepseek.com](https://platform.deepseek.com)）

### 1. 克隆并安装依赖

```bash
git clone https://github.com/Calora/news-aggregator.git
cd news-aggregator
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

### 2. 配置

```bash
cp backend/.env.example backend/.env
# 编辑 backend/.env，填入 DeepSeek API Key
```

最小配置只需要 `DEEPSEEK_API_KEY`，其余可选。

### 3. 启动

```bash
# Windows
start.bat

# macOS / Linux
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
cd frontend && npm run dev -- --host 0.0.0.0
```

浏览器打开 `http://localhost:5173`

### 可选：配置邮箱抓取

系统支持两种邮箱接入方式：

**Gmail API（推荐，国内需代理）**：
1. 创建 Google Cloud OAuth 桌面客户端 → 下载 `credentials.json` 放到 `backend/`
2. 运行 `python backend/setup_gmail_oauth.py` 完成授权
3. 在 `.env` 中配置 `GMAIL_CLIENT_ID` 等 + `HTTP_PROXY` 代理地址

**IMAP（QQ / 163 邮箱）**：
1. 邮箱设置中开启 IMAP/SMTP 并生成授权码
2. 在前端「数据源管理」页面添加邮箱账号

## 常见问题

**Q: 日报没有内容？**  
查看「数据源管理 → 抓取日志」，确认最近有抓取记录。如果没有，点「手动抓取」触发。

**Q: 文章全是英文？**  
检查 DeepSeek API Key 是否有效。系统依赖 AI 做翻译和分类。

**Q: 局域网分享？**  
前端启动在 `0.0.0.0` 后，局域网设备访问 `http://<你的IP>:5173`。

## License

Copyright 2026 QingSia

Licensed under the Apache License, Version 2.0.
