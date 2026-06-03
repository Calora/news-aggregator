"""RSS and web content fetcher."""
import re
from datetime import datetime
from html import unescape
from urllib.parse import urlparse

import feedparser
import httpx
from ..time_utils import beijing_now
from bs4 import BeautifulSoup

from ..models import WebSource, Article, FetchLog


def fetch_all_web(db_session) -> int:
    sources = db_session.query(WebSource).filter(WebSource.enabled == True).all()
    total_new = 0
    for src in sources:
        try:
            if src.source_type == "RSS":
                new_count = _fetch_rss(src, db_session)
            elif src.source_type == "ARXIV":
                new_count = _fetch_arxiv(src, db_session)
            else:
                new_count = _fetch_web(src, db_session)
            total_new += new_count
        except Exception as e:
            db_session.add(FetchLog(
                source_type=src.source_type,
                source_name=src.name,
                articles_found=0,
                articles_new=0,
                fetched_at=beijing_now(),
            ))
    db_session.commit()
    return total_new


def _clean_html(text: str) -> str:
    text = unescape(text)
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def _make_article(title: str, url: str, source_type: str, source_name: str,
                  content: str = None, pub_date: datetime = None) -> Article:
    return Article(
        title=_clean_html(title)[:1024],
        url=url[:2048] if url else "",
        source_type=source_type,
        source_name=source_name,
        content_preview=(content or "")[:500],
        full_content=content,
        publish_date=pub_date or beijing_now(),
        fetched_at=beijing_now(),
        domains=[],
        tags=[],
        format="行业动态",
        relevance_score=0,
    )


def _fetch_rss(src: WebSource, db_session) -> int:
    feed = feedparser.parse(src.url, agent="NewsDigest/1.0")
    if feed.bozo and not feed.entries:
        return 0

    found = len(feed.entries)
    new_count = 0
    existing_urls = {
        u[0] for u in
        db_session.query(Article.url).filter(Article.url.isnot(None)).all()
        if u[0]
    }

    for entry in feed.entries[:20]:
        link = entry.get("link", "")
        title = entry.get("title", "")

        if not title:
            continue
        if link and link in existing_urls:
            continue

        # Title-based dedup check
        from .deduplicator import is_duplicate
        if is_duplicate(title, link, db_session):
            continue

        pub_date = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            try:
                from time import mktime
                pub_date = datetime.fromtimestamp(mktime(entry.published_parsed))
            except Exception:
                pass
        if not pub_date and hasattr(entry, "updated_parsed") and entry.updated_parsed:
            try:
                from time import mktime
                pub_date = datetime.fromtimestamp(mktime(entry.updated_parsed))
            except Exception:
                pass

        content = ""
        if hasattr(entry, "summary"):
            content = _clean_html(entry.summary)[:1000]
        if hasattr(entry, "content") and entry.content:
            content = _clean_html(entry.content[0].value)[:1000]

        # Detect format from source name
        fmt = "行业动态"
        source_lower = src.name.lower()
        if any(k in source_lower for k in ["policy", "政策", "regulat", "gov",
                                               "网信", "工信", "数据局", "国务院", "部"]):
            fmt = "政策法规"
        elif any(k in source_lower for k in ["blog", "medium", "dev", "工程", "github", "ethresear", "hacker"]):
            fmt = "工程实践"
        elif any(k in source_lower for k in ["news", "block", "coindesk", "cointelegraph",
                                               "messari", "bankless", "decrypt"]):
            fmt = "行业动态"

        article = _make_article(title, link, "RSS", src.name, content, pub_date)
        article.format = fmt
        db_session.add(article)
        new_count += 1
        if link:
            existing_urls.add(link)

    db_session.add(FetchLog(
        source_type="RSS", source_name=src.name,
        articles_found=found, articles_new=new_count,
        fetched_at=beijing_now(),
    ))
    return new_count


def _fetch_arxiv(src: WebSource, db_session) -> int:
    """Fetch papers from arXiv API (e.g., cs.CR, cs.DC)."""
    import arxiv

    category = src.url.split("/")[-1] if "/" in src.url else src.url
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=15,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    new_count = 0
    existing_titles = {t[0] for t in db_session.query(Article.title).all()}

    try:
        for result in search.results():
            title = result.title.strip()
            if title in existing_titles:
                continue

            authors = ", ".join(a.name for a in result.authors[:5])
            content = result.summary.replace("\n", " ").strip()

            article = _make_article(
                title=title,
                url=result.entry_id,
                source_type="ARXIV",
                source_name=f"arXiv {category}",
                content=content,
                pub_date=result.published,
            )
            article.format = "学术论文"
            article.authors = authors
            db_session.add(article)
            new_count += 1
    except Exception:
        pass

    db_session.add(FetchLog(
        source_type="ARXIV", source_name=src.name,
        articles_found=new_count, articles_new=new_count,
        fetched_at=beijing_now(),
    ))
    return new_count


def _fetch_web(src: WebSource, db_session) -> int:
    """Basic web scraper for specific sites like Ingonyama blog."""
    try:
        resp = httpx.get(src.url, timeout=15, follow_redirects=True,
                         headers={"User-Agent": "NewsDigest/1.0"})
        resp.raise_for_status()
    except Exception:
        return 0

    soup = BeautifulSoup(resp.text, "lxml")
    articles_found = 0
    new_count = 0
    existing_titles = {t[0] for t in db_session.query(Article.title).all()}

    for link in soup.find_all("a", href=True):
        href = link["href"]
        text = link.get_text(strip=True)
        if not text or len(text) < 10:
            continue
        if text in existing_titles:
            continue

        if not href.startswith("http"):
            base = f"{urlparse(src.url).scheme}://{urlparse(src.url).netloc}"
            href = base + (href if href.startswith("/") else "/" + href)

        article = _make_article(
            title=text,
            url=href,
            source_type="WEB",
            source_name=src.name,
            content=text,
        )
        article.format = "工程实践"
        db_session.add(article)
        new_count += 1
        articles_found += 1

    db_session.add(FetchLog(
        source_type="WEB", source_name=src.name,
        articles_found=articles_found, articles_new=new_count,
        fetched_at=beijing_now(),
    ))
    return new_count
