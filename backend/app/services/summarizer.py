"""Standalone summarizer for individual articles (can be invoked from API).
The main summarization logic is in classifier.py as part of the pipeline.
This module provides a helper for re-summarization or direct API calls.
"""
from sqlalchemy.orm import Session
from ..models import Article
from .ai_client import chat_json

SUMMARY_PROMPT = """你是技术编辑。请将以下技术内容生成50-80字中文摘要。

要求:
1. 准确概括核心内容，不夸张不遗漏
2. 突出技术创新点（如有具体方案）
3. 对评分≥8的内容，附加一句技术视角推荐理由

标题: {title}
评分: {score}分
内容: {content}

返回JSON: {{"summary": "50-80字中文摘要", "reason": "推荐理由"}}"""


def summarize_article(article_id: int, db: Session) -> dict | None:
    """Re-summarize a single article."""
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return None

    content = (article.content_preview or "")[:1500]
    result = chat_json(SUMMARY_PROMPT.format(
        title=article.title,
        score=article.relevance_score,
        content=content,
    ))

    if "error" not in result:
        article.summary_cn = result.get("summary", "")
        article.reason = result.get("reason", "")
        db.commit()
        return article.to_dict()

    return None
