from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, text
from ..database import get_db
from ..models import Article
from ..schemas import ArticleResponse

router = APIRouter()


def _domain_filter_clause(domain_list: list[str]):
    """Build SQLite JSON filter: check if ANY domain in the list is in the JSON array."""
    if not domain_list:
        return None
    # Use json_each to check if any value in the domains JSON array matches
    conditions = []
    for d in domain_list:
        # SQLite json_each approach: EXISTS (SELECT 1 FROM json_each(domains) WHERE value = 'X')
        conditions.append(
            text("EXISTS (SELECT 1 FROM json_each(articles.domains) WHERE value = :domain)")
            .bindparams(domain=d)
        )
    return or_(*conditions) if len(conditions) > 1 else conditions[0]


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
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Article)

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
        for d in domain_list:
            query = query.filter(Article.domains.like(f'%\"{d}\"%'))

    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Article.title.contains(like),
                Article.summary_cn.contains(like),
            )
        )

    if date_from:
        query = query.filter(Article.publish_date >= date_from)
    if date_to:
        query = query.filter(Article.publish_date <= date_to + "T23:59:59")

    total = query.count()
    items = (
        query.order_by(Article.publish_date.desc())
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


@router.post("/bookmarks/group")
def group_bookmarks(db: Session = Depends(get_db)):
    """AI-group bookmarked articles by topic for writing."""
    from ..services.bookmark_grouper import group_bookmarks as do_group
    return do_group(db)


@router.post("/bookmarks/sync-to-feishu")
def sync_to_feishu(data: dict, db: Session = Depends(get_db)):
    """Sync selected bookmark groups to Feishu documents.
    Body: {"group_indices": [0, 1, ...]} — indices from grouping result."""
    from ..services.bookmark_grouper import group_bookmarks as do_group
    from ..services.feishu_service import create_doc, build_doc_blocks

    grouping = do_group(db)
    if "error" in grouping:
        return {"ok": False, "error": grouping["error"]}

    indices = data.get("group_indices", [])
    groups = grouping.get("groups", [])
    docs_created = []
    errors = []

    for idx in indices:
        if idx >= len(groups):
            continue
        group = groups[idx]
        try:
            blocks = build_doc_blocks(group)
            doc = create_doc(f"【写作素材】{group['topic']}", blocks)
            docs_created.append({"topic": group["topic"], "url": doc["url"], "article_count": len(group["articles"])})
        except Exception as e:
            errors.append({"topic": group["topic"], "error": str(e)})

    return {"ok": True, "docs_created": docs_created, "errors": errors}


@router.get("/bookmarks/test-feishu")
def test_feishu_connection():
    from ..services.feishu_service import test_connection
    ok, msg = test_connection()
    return {"ok": ok, "message": msg}
