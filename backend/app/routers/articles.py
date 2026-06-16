from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from ..database import get_db
from ..models import Article
from ..schemas import ArticleResponse

router = APIRouter()


def _domain_filter_clauses(domain_list: list[str]):
    """Build SQLite JSON filters requiring every selected domain to be present."""
    clauses = []
    for index, domain in enumerate(domain_list):
        param_name = f"domain_{index}"
        clauses.append(
            text(f"EXISTS (SELECT 1 FROM json_each(articles.domains) WHERE value = :{param_name})")
            .bindparams(**{param_name: domain})
        )
    return clauses


@router.get("/articles")
def list_articles(
    domains: Optional[str] = Query(None),
    formats: Optional[str] = Query(None),
    tags: Optional[str] = Query(None),
    score_min: int = Query(7),
    score_max: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None),
    sort_by: str = Query("publish_date"),
    sort_order: str = Query("desc"),
    limit: Optional[int] = Query(None, ge=1, le=100),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Article)
    if limit is not None:
        page_size = limit

    # Hard filter: only show score >= 7 (user doesn't want junk)
    query = query.filter(Article.relevance_score >= score_min)
    if score_max is not None:
        query = query.filter(Article.relevance_score <= score_max)

    # Format — direct column
    format_list = [f.strip() for f in formats.split(",")] if formats else []
    if format_list:
        query = query.filter(Article.format.in_(format_list))

    # Domain — AND logic: ALL selected domains must be present
    # Use LIKE with quotes to match exact JSON array elements (avoid partial matches like "AI" in "Blockchain")
    domain_list = [d.strip() for d in domains.split(",")] if domains else []
    if domain_list:
        for domain_clause in _domain_filter_clauses(domain_list):
            query = query.filter(domain_clause)

    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    for tag in tag_list:
        query = query.filter(Article.tags.like(f'%\"{tag}\"%'))

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Article.title.like(like),
                Article.summary_cn.like(like),
                Article.content_preview.like(like),
                Article.tags.like(like),
            )
        )

    if date_from:
        query = query.filter(Article.publish_date >= date_from)
    if date_to:
        query = query.filter(Article.publish_date <= date_to + "T23:59:59")

    total = query.count()
    sort_columns = {
        "publish_date": Article.publish_date,
        "fetched_at": Article.fetched_at,
        "relevance_score": Article.relevance_score,
        "id": Article.id,
    }
    sort_column = sort_columns.get(sort_by, Article.publish_date)
    sort_expr = sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()
    items = (
        query.order_by(sort_expr)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return ArticleResponse(
        items=[item.to_dict() for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/articles/{article_id}")
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return {"error": "not found"}
    return article.to_dict()


@router.get("/bookmarks")
def list_bookmarks(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(Article).filter(Article.is_bookmarked == True)
    total = query.count()
    items = query.order_by(Article.publish_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [a.to_dict() for a in items], "total": total, "page": page, "page_size": page_size}


@router.post("/articles/{article_id}/bookmark")
def toggle_bookmark(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if not article:
        return {"error": "not found"}
    article.is_bookmarked = not article.is_bookmarked
    db.commit()
    return {"ok": True, "bookmarked": article.is_bookmarked}


@router.post("/bookmarks/sync-to-feishu")
def sync_to_feishu(data: dict | None = None, db: Session = Depends(get_db)):
    """Sync ALL bookmarked articles to Feishu.
    - Material doc: all bookmarks (title, summary, tags, url, score)
    - Topic doc: AI-generated article topic suggestions based on materials
    Only syncs articles that haven't been synced before."""
    from datetime import date
    from ..services.feishu_service import append_to_doc, clear_doc, _h1, _h2, _p, _rich, _empty
    from ..services.ai_client import chat
    from ..config import settings

    material_doc_id = settings.feishu_material_doc_id
    topic_doc_id = settings.feishu_topic_doc_id

    bookmarks = db.query(Article).filter(
        Article.is_bookmarked == True,
        Article.relevance_score >= 7,
    ).order_by(Article.publish_date.desc()).all()

    if not bookmarks:
        return {"ok": False, "error": "没有收藏的文章"}

    new_articles = [a for a in bookmarks if not a.synced_to_feishu]
    already_synced = len(bookmarks) - len(new_articles)

    # ── Doc 1: Append new material to existing doc ──
    material_url = None
    if new_articles and material_doc_id:
        date_header = _p(f"━━ 📅 同步日期：{date.today().isoformat()} ━━")
        blocks = [date_header, _empty()]
        for a in new_articles:
            blocks.append(_h2(a.title))
            if a.url:
                blocks.append(_rich([
                    {"text_run": {"content": "链接：", "text_element_style": {"bold": True}}},
                    {"text_run": {"content": a.url or "", "text_element_style": {"link": {"url": a.url or ""}}}},
                ]))
            if a.summary_cn:
                blocks.append(_p(f"摘要：{a.summary_cn}"))
            tags_str = " · ".join(a.tags or [])
            if tags_str:
                blocks.append(_p(f"标签：{tags_str}"))
            blocks.append(_p(f"领域：{' · '.join(a.domains or [])}　｜　评分：★{a.relevance_score}　｜　来源：{a.source_name}"))
            blocks.append(_empty())

        doc_info = append_to_doc(material_doc_id, blocks)
        material_url = doc_info["url"]
        for a in new_articles:
            a.synced_to_feishu = True
        db.commit()
    elif material_doc_id:
        material_url = f"https://calosia.feishu.cn/docx/{material_doc_id}"

    # ── Doc 2: Clear + regenerate topic doc ──
    topic_url = None
    if topic_doc_id:
        all_articles_text = "\n\n".join([
            f"[{i+1}] {a.title}\n链接: {a.url or '无'}\n摘要: {a.summary_cn or a.content_preview or ''[:150]}\n标签: {', '.join(a.tags or [])}"
            for i, a in enumerate(bookmarks)
        ])

        topic_prompt = f"""你是资深技术编辑。基于以下收藏的技术文章，推荐 5-8 个公众号文章选题。

对每个选题，输出：
- title: 吸引人的标题（15-25字，要有悬念或明确判断）
- thesis: 文章核心观点（一句话说清楚要论证什么）
- materials: 使用哪些素材编号（如 [1, 3, 5]）
- angle: 写作角度（从什么切入点展开论述）

素材：
{all_articles_text[:4000]}

返回 JSON: {{"topics": [{{"title": "...", "thesis": "...", "materials": [1,2], "angle": "..."}}]}}"""

        topic_result = chat(topic_prompt, "You are a senior tech editor. Always reply with valid JSON only.")
        import json, re
        m = re.search(r"```(?:json)?\s*(\[.*?\]|\{.*?\})\s*```", topic_result, re.DOTALL)
        if m:
            topic_result = m.group(1)
        try:
            topics_data = json.loads(topic_result)
            if isinstance(topics_data, dict):
                topics = topics_data.get("topics", [])
            else:
                topics = topics_data
        except json.JSONDecodeError:
            topics = []

        topic_blocks = [_h1("公众号选题推荐"), _p(f"基于 {len(bookmarks)} 篇收藏文章生成以下选题（{date.today().isoformat()} 更新）："), _empty()]
        for i, t in enumerate(topics[:8], 1):
            topic_blocks.append(_h2(f"选题 {i}：{t.get('title', '')}"))
            topic_blocks.append(_p(f"核心观点：{t.get('thesis', '')}"))
            materials = t.get('materials', [])
            if materials:
                topic_blocks.append(_p("参考素材："))
                for m_id in materials:
                    if isinstance(m_id, int) and 1 <= m_id <= len(bookmarks):
                        bm = bookmarks[m_id - 1]
                        url = bm.url or ''
                        topic_blocks.append(_rich([
                            {"text_run": {"content": f"[{m_id}] {bm.title[:60]}", "text_element_style": {"bold": True}}},
                        ]))
                        if url:
                            topic_blocks.append(_rich([
                                {"text_run": {"content": url, "text_element_style": {"link": {"url": url}}}},
                            ]))
                        if bm.summary_cn:
                            topic_blocks.append(_p(f"    {bm.summary_cn[:120]}"))
            topic_blocks.append(_p(f"写作角度：{t.get('angle', '')}"))
            topic_blocks.append(_empty())

        clear_doc(topic_doc_id)
        doc_info = append_to_doc(topic_doc_id, topic_blocks)
        topic_url = doc_info["url"]

    return {
        "ok": True,
        "total_bookmarks": len(bookmarks),
        "new_synced": len(new_articles),
        "already_synced": already_synced,
        "material_doc": material_url,
        "topic_doc": topic_url,
    }


@router.get("/bookmarks/test-feishu")
def test_feishu_connection():
    from ..services.feishu_service import test_connection
    ok, msg = test_connection()
    return {"ok": ok, "message": msg}
