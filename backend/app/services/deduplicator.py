"""Article deduplication using title similarity and URL matching."""
import re
from datetime import datetime, timedelta
from ..time_utils import beijing_now
from sqlalchemy.orm import Session
from ..models import Article


def is_duplicate(title: str, url: str, db: Session) -> bool:
    """Check if a new article (not yet persisted) would be a duplicate.
    Call BEFORE saving to DB. Returns True if duplicate exists.
    """
    # 1. Exact URL match
    if url:
        existing = db.query(Article).filter(Article.url == url).first()
        if existing:
            return True

    # 2. Title similarity check (no time window — check all)
    title_tokens = _tokenize(title)
    if len(title_tokens) < 2:
        return False

    # Check against recent articles (7 days)
    since = beijing_now() - timedelta(days=7)
    recent = db.query(Article).filter(Article.fetched_at >= since).all()

    for existing in recent:
        existing_tokens = _tokenize(existing.title)
        sim = _jaccard(title_tokens, existing_tokens)
        if sim > 0.60:
            return True

    return False


def cleanup_duplicates(db: Session) -> int:
    """Remove duplicate articles (keep the one with highest score, or earliest)."""
    all_articles = db.query(Article).order_by(Article.id.asc()).all()
    to_delete = set()
    checked = []
    seen_urls = set()

    for article in all_articles:
        # URL-based dedup (exact match)
        if article.url:
            if article.url in seen_urls:
                to_delete.add(article.id)
                continue
            seen_urls.add(article.url)

        title_tokens = _tokenize(article.title)
        if len(title_tokens) < 2:
            continue

        is_dup = False
        for prev in checked:
            prev_tokens = _tokenize(prev.title)
            sim = _jaccard(title_tokens, prev_tokens)
            if sim > 0.60:
                if article.relevance_score > prev.relevance_score:
                    to_delete.add(prev.id)
                    checked.remove(prev)
                    checked.append(article)
                else:
                    to_delete.add(article.id)
                is_dup = True
                break

        if not is_dup:
            checked.append(article)

    if to_delete:
        for aid in to_delete:
            db.query(Article).filter(Article.id == aid).delete()
        db.commit()

    return len(to_delete)


def _tokenize(text: str) -> set[str]:
    """Simple word tokenization for Chinese + English."""
    text = text.lower()
    words = re.findall(r"[a-z0-9]+|[一-鿿]", text)
    return set(words)


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0
    return len(a & b) / len(a | b)
