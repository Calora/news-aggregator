"""AI-powered bookmark grouping — cluster related articles for writing."""
import json
from sqlalchemy.orm import Session
from ..models import Article
from .ai_client import chat_json


GROUP_PROMPT = """你是技术编辑。以下是你收藏的技术文章，请按"能否作为同一篇文章的写作素材"进行分组。

每篇文章提供了标题、摘要、标签和评分。分组原则：
1. 主题相同或高度相关的文章放到同一组
2. 一篇文章可以属于多个组（如果确实跨主题）
3. 每组至少 2 篇文章，单篇文章不要单独成组
4. 不相关的文章不要强行分组，放入 "ungrouped"
5. 为每组起一个主题名（topic），10 字以内
6. 为每组推荐 2-3 个公众号文章标题（吸引人、有悬念、点出核心判断）

文章列表：
{articles_json}

返回 JSON:
{{"groups": [
  {{"topic": "主题名", "article_ids": [1, 2], "suggested_titles": ["标题A", "标题B", "标题C"]}},
  ...
], "ungrouped": [5, 6]}}"""


def group_bookmarks(db: Session) -> dict:
    """Group bookmarked articles by topic using AI. Returns grouping result."""
    articles = db.query(Article).filter(Article.is_bookmarked == True, Article.relevance_score >= 7).all()
    if len(articles) < 2:
        return {"groups": [], "ungrouped": [a.id for a in articles], "articles": [a.to_dict() for a in articles]}

    # Build article summaries for prompt
    article_entries = []
    for a in articles:
        entry = {
            "id": a.id,
            "title": a.title,
            "summary": (a.summary_cn or a.content_preview or "")[:150],
            "tags": a.tags or [],
            "score": a.relevance_score,
            "domains": a.domains or [],
        }
        article_entries.append(entry)

    prompt = GROUP_PROMPT.format(articles_json=json.dumps(article_entries, ensure_ascii=False, indent=2))
    result = chat_json(prompt)

    if "error" in result:
        return {"error": result.get("error", "AI grouping failed"), "groups": [], "ungrouped": [], "articles": [a.to_dict() for a in articles]}

    # Build full article dicts for response
    article_map = {a.id: a.to_dict() for a in articles}

    groups = result.get("groups", [])
    for g in groups:
        g["articles"] = [article_map.get(aid) for aid in g.get("article_ids", []) if article_map.get(aid)]

    ungrouped = result.get("ungrouped", [])
    ungrouped_articles = [article_map.get(aid) for aid in ungrouped if article_map.get(aid)]

    return {
        "groups": groups,
        "ungrouped_ids": ungrouped,
        "ungrouped_articles": ungrouped_articles,
        "total_bookmarks": len(articles),
    }
