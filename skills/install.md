---
name: newsdigest
description: 一键部署 AI 驱动的技术新闻聚合器，自动抓取、分类、生成日报
---

# NewsDigest — AI 技术新闻聚合器

面向区块链、AI、密码学方向的技术新闻聚合工具，每日自动生成精选日报。

## 安装

用户说"帮我安装 NewsDigest"时，执行以下步骤：

### 1. 检查环境

```bash
python --version   # 需要 3.10+
node --version     # 需要 18+
```

如果缺少依赖，先引导用户安装。

### 2. 克隆项目

```bash
git clone https://github.com/QingSia/news-aggregator.git
cd news-aggregator
```

### 3. 安装依赖

```bash
pip install -r backend/requirements.txt
cd frontend && npm install && cd ..
```

### 4. 配置 DeepSeek API Key

```bash
cp backend/.env.example backend/.env
```

然后帮用户编辑 `backend/.env`，设置 `DEEPSEEK_API_KEY=用户提供的key`。

如果用户还没有 DeepSeek Key，引导去 https://platform.deepseek.com 注册获取。

### 5. 启动

```bash
# 后端（新终端窗口）
cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端（新终端窗口）
cd frontend && npm run dev -- --host 0.0.0.0
```

浏览器打开 `http://localhost:5173` 即可使用。

### 可选：配置邮箱抓取

如果用户需要从 Gmail 拉取邮件中的新闻链接：
1. 在 Google Cloud Console 创建 OAuth 桌面客户端
2. 下载 `credentials.json` 放到 `backend/`
3. 运行 `python backend/setup_gmail_oauth.py` 完成授权
4. 在 `.env` 中配置 Gmail OAuth 凭证和 HTTP_PROXY

## 使用

- **每日日报**：首页自动显示当天精选
- **全部动态**：浏览/筛选所有文章，支持领域、标签、类型筛选
- **数据源管理**：管理 RSS/网页/邮箱数据源，手动抓取
- **我的收藏**：收藏感兴趣的文章

## 常见问题

### 日报没内容
→ 数据源管理 → 手动抓取，等待完成

### 文章没中文
→ 检查 DEEPSEEK_API_KEY 是否配置正确

### 局域网分享
→ 前端启动加 `--host 0.0.0.0`，其他设备访问 `http://<IP>:5173`
