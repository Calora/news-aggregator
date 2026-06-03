# 📰 NewsDigest

> 🤖 AI 替你读新闻 — 自动抓取 · 智能分类 · 每日精选日报

每天醒来，AI 已经帮你挑好了最值得读的 10 条技术新闻。不再被几百封邮件和几十个 RSS 源淹没。

<p align="center">
  <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square" alt="FastAPI">
  <img src="https://img.shields.io/badge/Frontend-React-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React">
  <img src="https://img.shields.io/badge/AI-DeepSeek-4B6BFB?style=flat-square" alt="DeepSeek">
  <img src="https://img.shields.io/badge/License-Apache%202.0-blue?style=flat-square" alt="License">
</p>

---

## ✨ 为什么你需要这个

你订阅了十几个新闻源，邮箱里塞满了 newsletter。每天光是扫标题就要花半小时，更不用说判断哪篇值得细读。

NewsDigest 帮你做三件事：

1. 📥 **自动收** — RSS + 网页 + 邮件三通道抓取，你不用再打开任何邮箱和阅读器
2. 🧠 **帮你读** — DeepSeek 大模型自动翻译英文、分类打标签、评分过滤噪音
3. 📋 **挑重点** — 每天早上 8 点，一份 ≤10 条精选的日报已经整装待发

---

## 🪄 看一眼长什么样

| 📅 每日日报 | 📋 全部动态 |
|-------------|------------|
| 左侧日期归档，每天 4 个领域分组 | 多维度筛选，卡片式浏览 |
| 每篇带评分 + 推荐理由 + 点题标签 | 按领域 / 类型 / 标签自由组合 |
| 早 8 点自动生成，未读先看 | 7 分以下自动过滤，不浪费你的注意力 |

---

## 🛠 技术栈

```
📡 数据层                        🧠 AI 层                         🖥 展示层
 ┌──────────┐                 ┌──────────┐                 ┌──────────┐
 │ RSS      │                 │ DeepSeek │                 │ React    │
 │ Gmail API│  ──→ FastAPI ──→│   分类    │  ──→ REST ──→ │ Tailwind │
 │ IMAP     │                 │   评分    │                 │ Vite     │
 │ 网页抓取 │                 │   翻译    │                 │          │
 └──────────┘                 └──────────┘                 └──────────┘
```

---

## 🚀 3 分钟跑起来

### 你需要准备

- 🐍 Python 3.10+
- 🟢 Node.js 18+
- 🔑 DeepSeek API Key → [免费注册获取](https://platform.deepseek.com) 只需 10 块钱能用一个月

### 安装

```bash
# 克隆
git clone https://github.com/Calora/news-aggregator.git
cd news-aggregator

# 装依赖
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..

# 配置
cp backend/.env.example backend/.env
# 编辑 backend/.env，填一行：DEEPSEEK_API_KEY=sk-你的key
```

### 启动

```bash
# Windows 一键
start.bat

# macOS / Linux
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
cd frontend && npm run dev -- --host 0.0.0.0
```

打开 `http://localhost:5173`，第一次运行会自动批量抓取所有信源。

---

## 📦 项目结构

```
news-aggregator/
├── ⚡ start.bat              # Windows 一键启动三件套
├── 🩺 health_check.py        # 外部健康巡检，每天自检4次
├── 🔧 backend/               # Python FastAPI
│   ├── .env.example          # 配置模板（只需填 API Key）
│   └── app/
│       ├── main.py           # 🚪 入口
│       ├── models.py         # 📊 5 张数据表
│       ├── routers/          # 🔀 API 路由
│       └── services/
│           ├── web_fetcher.py     # 🌐 RSS + 网页抓取
│           ├── email_fetcher.py   # ✉️ IMAP 邮件
│           ├── gmail_fetcher.py   # 📨 Gmail API（走代理）
│           ├── classifier.py      # 🤖 AI 分类 + 评分 + 翻译
│           ├── deduplicator.py    # 🧹 去重
│           └── pipeline.py        # ⛓ 完整流水线
├── 🎨 frontend/              # React + Tailwind
│   └── src/
│       ├── pages/            # 📄 4 个页面
│       └── components/       # 🧩 UI 组件
└── 🧠 skills/                # Claude Code Skill 定义
```

---

## 🔌 可选：接入私人邮箱

如果想把 Medium Daily Digest、InfoQ 等邮件内容也自动纳入：

| 方式 | 难度 | 适合 |
|------|------|------|
| 📨 Gmail API | ⭐⭐⭐ | 有梯子，稳定好用 |
| ✉️ QQ / 163 IMAP | ⭐ | 国内直连，授权码即用 |

在前端「数据源管理」页面即可配置，不需要改代码。

---

## 💬 FAQ

<details>
<summary>日报为啥是空的？</summary>

去「数据源管理 → 手动抓取」点一下，等 10-30 秒。如果还是空，检查 DeepSeek Key 是否有效。
</details>

<details>
<summary>为什么文章全是英文？</summary>

DeepSeek API Key 没配或失效。系统依赖 AI 做翻译和中文摘要。
</details>

<details>
<summary>想和同事一起看？</summary>

前端启动在 `0.0.0.0:5173`，局域网任何设备访问 `http://<你的IP>:5173` 即可。
</details>

<details>
<summary>邮件拉取报错？</summary>

Gmail API 需要 OAuth 授权，跑 `python backend/setup_gmail_oauth.py` 完成。QQ/163 需要去邮箱设置里生成授权码（不是登录密码）。
</details>

---

## 📄 License

Copyright © 2026 [QingSia](https://github.com/Calora) · Apache License 2.0

---

<p align="center">
  <sub>Built with ❤️ + 🧠 + ⛓️</sub>
</p>
