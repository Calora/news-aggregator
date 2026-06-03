"""AI-powered 3D classification, scoring, summarization, and filtering."""
import re
from datetime import datetime
from sqlalchemy.orm import Session
from ..models import Article
from .ai_client import chat_json

PRICE_KEYWORDS = [
    "涨跌", "行情", "走势", "K线", "多空", "点位", "爆仓", "合约",
    "price", "pump", "dump", "bullish", "bearish", "rally",
    "空投", "代币", "MEME", "NFT.*发售", "IDO", "IEO", "mint",
    "airdrop", "token.*sale", "whitelist",
]

CLASSIFY_PROMPT = """你是区块链+AI领域的研究员。对以下内容进行分类。最关键的是：只收录与指定领域明确相关的文章。

## 领域 (domains, 1-2个)
- Blockchain: 仅限公链/L2/共识/跨链/EVM/Solidity/智能合约
- AI: 仅限大模型/Agent/训练推理/AI安全/AI Token
- 数字资产: 仅限加密货币监管/交易所牌照/稳定币合规/CBDC/数字资产立法
- Crypto & Privacy: 仅限ZK证明/MPC/FHE/TEE/后量子密码/GPU密码学加速。注意：苹果/iOS/Android安全、加密库形式化验证、MDM绕过、通用渗透测试、应用安全漏洞不属于此领域

## 不相关内容（直接标记为 irrelevant）
以下话题不属于以上任何领域，必须标记为 irrelevant：
- GitHub/GitLab内部管理、软件供应链安全（非区块链专用）
- Docker/容器/K8s/通用运维/容量规划
- 传统数据库/消息队列/CPU设计（非区块链专用）
- 通用软件漏洞（非智能合约），包括iOS/Android/MDM绕过
- 非AI的逆向工程/二进制分析
- 普通应用安全/渗透测试（非区块链专用）
- 招聘/人事/公司管理
- 纯行情/价格/交易/空投/代币发售
- 通用数据编码/序列化方案（Varint/整数编码/BaseXX等，非区块链专用）
- 通用压缩/存储/索引算法
- 通用加密库的形式化验证（除非明确用于ZK/MPC/区块链）
- 通用分布式一致性算法（非区块链共识专用）
- 摄像头/安防/IoT硬件（非区块链专用）
- 操作系统/内核/驱动（非区块链专用）

## 判断原则
1. 内容必须与区块链/AI/数字资产/密码学明显直接相关
2. 仅有微弱联系或关键词巧合 → irrelevant
3. 不确定时保守处理 → irrelevant
4. Blockchain分类严格要求：文章标题或摘要中必须出现区块链/以太坊/共识/智能合约/EVM/跨链等明确概念，仅凭"分布式""加密""编码"等通用词汇不够

## 格式 (format, 选1个)
- 工程实践: 技术博客/开源项目/协议提案/性能测试
- 政策法规: 政府发文/监管法律
- 行业动态: 新闻快讯/产品发布/投融资

## 技术标签 (tags, 提取1-5个具体技术关键词)

标题: {title}
正文预览: {content}

返回JSON: {{"domains": [...] 或 "irrelevant" 如果不相关, "format": "...", "tags": [...]}}"""


SCORE_PROMPT = """你是区块链+AI领域的资深研究者（非投资者）。从技术价值角度评分(0-10整数)。

## 评分标准（新闻/博客/行业动态）
10: 突破性进展（主网关键升级、重大安全发现、AI+区块链新范式）
9: 重要进展（协议升级、大模型重大发布、重要政策出台）
8: 有价值（技术改进方案、新工具、深度分析）
7: 值得关注（提案/讨论、常规产品更新）
6以下: 低价值（行情、营销、空投、NFT）

## 论文专项评分（format=学术论文时，从以下维度严格评判）
- 发表单位：作者来自MIT/Stanford/CMU/Berkeley/清华/北大/浙大/上交/中科院/ETH/Oxford/Cornell等顶尖机构→加分；作者单位不明或来自非研究机构→减分
- 实验充分性：有完整实验设计、对比基线、性能数据、开源代码→加分；仅有理论描述无实验验证→大幅减分，评4-6分
- 创新性：提出新方法/新范式/新理论→加分；仅调参/简单组合→减分
- 论文载体：CCF-A/CORE A*会议期刊→基准9分起评；arXiv预印本→需更严格判断质量

## 灌水论文特征（直接给5分以下）
- "基于XX的YY优化"类标题，无实质创新
- 实验仅在小规模数据集上跑，无对比基线
- 作者单位未知或来自二线以下机构
- 论文长度极短，无系统设计章节
- 仅总结已有工作，无自己方法

标题: {title}
作者: {authors}
分类: domains={domains}, format={format}, tags={tags}
摘要: {content}

返回JSON: {{"score": 整数0到10, "reason": "≤15字评分理由"}}"""


SUMMARY_PROMPT = """你是技术编辑。请将以下内容翻译并摘要，全部输出为中文。

要求:
1. 如果标题是英文，翻译成简洁准确的中文标题
2. 生成50-80字中文摘要，准确概括核心内容
3. 突出技术创新点（如有具体方案/数据）
4. 对评分≥7的内容，附加一句技术视角推荐理由
5. 学术论文需提及方法名称或技术路线

原标题: {title}
评分: {score}分
内容: {content}

返回JSON: {{"title_cn": "中文标题", "summary": "50-80字中文摘要", "reason": "推荐理由（评分<7可为空）"}}"""


def process_unclassified(db: Session) -> int:
    """Process all articles that haven't been classified yet."""
    # Priority 1: score=0 articles (never processed)
    articles = db.query(Article).filter(
        Article.relevance_score == 0,
    ).limit(30).all()

    processed = 0
    for article in articles:
        try:
            if _process_one(article, db):
                processed += 1
        except Exception:
            pass

    # Priority 2: high-score articles without Chinese summary or domains (CCF-A etc.)
    need_summary = db.query(Article).filter(
        Article.relevance_score >= 7,
        Article.summary_cn == None,
    ).limit(20).all()

    for article in need_summary:
        try:
            if _classify_only(article):
                processed += 1
        except Exception:
            pass

    # Priority 3: articles with English titles that need translation
    for article in list(need_summary)[:]:
        if _is_mostly_english(article.title) and not article.summary_cn:
            try:
                if _classify_only(article):
                    processed += 1
            except Exception:
                pass

    db.commit()
    return processed


def _classify_only(article: Article) -> bool:
    """Classify and summarize without changing the score (for pre-scored articles like CCF-A papers)."""
    content = (article.content_preview or "")[:2000]

    classify_result = chat_json(CLASSIFY_PROMPT.format(
        title=article.title,
        content=content,
    ))
    if "error" in classify_result:
        return False

    article.domains = classify_result.get("domains", ["Blockchain"])
    article.format = classify_result.get("format", "学术论文")
    article.tags = classify_result.get("tags", [])

    # Only adjust score within [8, 10] range for CCF-A papers
    score_result = chat_json(SCORE_PROMPT.format(
        title=article.title,
        authors=article.authors or "未知",
        domains=article.domains,
        format=article.format,
        tags=article.tags,
        content=content,
    ))
    if "error" not in score_result:
        score = score_result.get("score", article.relevance_score)
        if isinstance(score, (int, float)):
            score = int(score)
            # Floor at 8 for CCF-A papers
            article.relevance_score = max(8, min(10, score))
        article.reason = score_result.get("reason", "")

    # Generate Chinese summary
    summary_result = chat_json(SUMMARY_PROMPT.format(
        title=article.title,
        score=article.relevance_score,
        content=content,
    ))
    if "error" not in summary_result:
        title_cn = summary_result.get("title_cn", "")
        article.summary_cn = summary_result.get("summary", "")
        if title_cn and _is_mostly_english(article.title):
            article.title = title_cn

    return True


def _process_one(article: Article, db: Session) -> bool:
    """Run full AI pipeline on a single article."""
    content = (article.content_preview or "")[:2000]

    # Step 1: Filter out trading/speculation content
    if _is_price_noise(article.title):
        article.domains = ["Blockchain"]
        article.format = "行业动态"
        article.tags = []
        article.relevance_score = 1
        article.summary_cn = "行情/投机类内容，已自动过滤"
        return True

    # Step 2: 3D Classification
    classify_result = chat_json(CLASSIFY_PROMPT.format(
        title=article.title,
        content=content,
    ))
    if "error" in classify_result:
        return False

    # Handle irrelevant content
    if classify_result.get("domains") == "irrelevant" or "irrelevant" in str(classify_result.get("domains", [])):
        article.domains = []
        article.format = "行业动态"
        article.tags = []
        article.relevance_score = 1
        article.summary_cn = "与关注领域无关，已自动过滤"
        return True

    article.domains = classify_result.get("domains", [])
    # If domains is still "irrelevant" or empty, filter out
    if not article.domains or article.domains == "irrelevant":
        article.domains = []
        article.relevance_score = 1
        article.summary_cn = "与关注领域无关"
        return True

    article.format = classify_result.get("format", "行业动态")
    article.tags = classify_result.get("tags", [])

    # Step 3: Scoring (with paper quality dimensions for academic papers)
    score_result = chat_json(SCORE_PROMPT.format(
        title=article.title,
        authors=article.authors or "未知",
        domains=article.domains,
        format=article.format,
        tags=article.tags,
        content=content,
    ))
    if "error" in score_result:
        return False

    score = score_result.get("score", 5)
    if not isinstance(score, int):
        try:
            score = int(score)
        except (ValueError, TypeError):
            score = 5

    if _is_price_noise(article.title):
        score = min(score, max(score - 3, 1))

    article.relevance_score = max(0, min(10, score))
    article.reason = score_result.get("reason", "")

    # Step 4: Chinese title + summary (for all articles, regardless of score)
    summary_result = chat_json(SUMMARY_PROMPT.format(
        title=article.title,
        score=article.relevance_score,
        content=content,
    ))
    if "error" not in summary_result:
        title_cn = summary_result.get("title_cn", "")
        article.summary_cn = summary_result.get("summary", "")
        if article.relevance_score >= 7:
            article.reason = summary_result.get("reason") or article.reason
        # If English title, replace with Chinese; otherwise keep original
        if title_cn and _is_mostly_english(article.title):
            article.title = title_cn

    return True


def _is_price_noise(title: str) -> bool:
    for kw in PRICE_KEYWORDS:
        if re.search(kw, title, re.IGNORECASE):
            return True
    return False


def _is_mostly_english(text: str) -> bool:
    """Check if text is predominantly ASCII/English."""
    ascii_chars = sum(1 for c in text if ord(c) < 128)
    return ascii_chars / max(len(text), 1) > 0.5
