from datetime import date, datetime, timedelta
from ..time_utils import beijing_now, beijing_today
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Article, DailyReport

router = APIRouter()

DOMAIN_ORDER = ["Blockchain", "AI", "数字资产", "Crypto & Privacy"]


def _article_dedupe_key(article: Article) -> str:
    from ..services.deduplicator import _normalize_url
    if article.url:
        return f"url:{_normalize_url(article.url)}"
    return f"title:{article.title.strip().lower()}"

@router.get("/report/list")
def list_reports(db: Session = Depends(get_db)):
    """Return all daily reports with date and headline (first article title)."""
    reports = db.query(DailyReport).order_by(DailyReport.date.desc()).limit(60).all()
    result = []
    for report in reports:
        headline = ""
        if report.article_ids:
            first_article = db.query(Article).filter(Article.id == report.article_ids[0]).first()
            if first_article:
                headline = first_article.title[:40]
        result.append({
            "date": report.date.isoformat(),
            "headline": headline,
            "article_count": len(report.article_ids or []),
        })
    return result


@router.get("/report/today")
def get_today_report(db: Session = Depends(get_db)):
    today = beijing_today()
    report = db.query(DailyReport).filter(DailyReport.date == today).first()
    if not report:
        return {"date": today.isoformat(), "sections": [], "article_ids": []}

    article_ids = report.article_ids or []
    articles = db.query(Article).filter(Article.id.in_(article_ids)).all() if article_ids else []
    article_map = {a.id: a.to_dict() for a in articles}
    return report.to_dict(article_map)


@router.get("/report/{report_date}")
def get_report(report_date: str, db: Session = Depends(get_db)):
    report = db.query(DailyReport).filter(DailyReport.date == report_date).first()
    if not report:
        return {"date": report_date, "sections": [], "article_ids": []}

    article_ids = report.article_ids or []
    articles = db.query(Article).filter(Article.id.in_(article_ids)).all() if article_ids else []
    article_map = {a.id: a.to_dict() for a in articles}
    return report.to_dict(article_map)
    """Return all daily reports with date and headline (first article title)."""
    reports = db.query(DailyReport).order_by(DailyReport.date.desc()).limit(60).all()
    result = []
    for report in reports:
        headline = ""
        if report.article_ids:
            first_article = db.query(Article).filter(Article.id == report.article_ids[0]).first()
            if first_article:
                headline = first_article.title[:40]
        result.append({
            "date": report.date.isoformat(),
            "headline": headline,
            "article_count": len(report.article_ids or []),
        })
    return result


@router.post("/report/generate")
def generate_report(target_date: Optional[str] = Query(None), db: Session = Depends(get_db)):
    report_date = date.fromisoformat(target_date) if target_date else beijing_today()
    return do_generate_report(db, report_date)


def do_generate_report(db: Session, report_date: date):

    existing = db.query(DailyReport).filter(DailyReport.date == report_date).first()
    if existing:
        db.delete(existing)
        db.commit()

    # Report covers: yesterday 8:00 → today 8:00 (naive datetime, SQLite compatible)
    today_8am = datetime(report_date.year, report_date.month, report_date.day, 8, 0, 0)
    date_start = today_8am - timedelta(days=1)  # yesterday 8am
    date_end = today_8am                          # today 8am

    articles = (
        db.query(Article)
        .filter(
            Article.relevance_score >= 7,
            Article.publish_date >= date_start,
            Article.publish_date < date_end,
        )
        .order_by(Article.relevance_score.desc())
        .all()
    )

    sections = []
    all_ids = []
    used_ids = set()  # Track articles already placed in a section
    used_keys = set()  # Track duplicate URLs/titles across sections

    for domain in DOMAIN_ORDER:
        domain_articles = [
            a for a in articles
            if domain in (a.domains or []) and a.id not in used_ids
        ]
        if not domain_articles:
            continue

        domain_articles.sort(key=lambda a: a.relevance_score, reverse=True)
        top = []
        for article in domain_articles:
            key = _article_dedupe_key(article)
            if key in used_keys:
                continue
            top.append(article)
            used_keys.add(key)
            if len(top) >= 3:
                break
        if not top:
            continue
        section_article_ids = [a.id for a in top]
        used_ids.update(section_article_ids)
        all_ids.extend(section_article_ids)

        sections.append({
            "domain": domain,
            "article_ids": section_article_ids,
        })

        if len(all_ids) >= 10:
            break

    all_ids = all_ids[:10]

    report = DailyReport(
        date=report_date,
        sections=sections,
        article_ids=all_ids,
        generated_at=beijing_now(),
    )
    db.add(report)

    for article in articles:
        article.is_daily_pick = article.id in all_ids

    db.commit()

    article_map = {a.id: a.to_dict() for a in articles if a.id in all_ids}
    return report.to_dict(article_map)
