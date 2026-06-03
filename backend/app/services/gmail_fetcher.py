"""Gmail API fetcher — uses REST API via requests (proxy-friendly)."""
import base64
import re
from datetime import datetime, timedelta
from email.header import decode_header
from email.utils import parsedate_to_datetime

import requests as http
from bs4 import BeautifulSoup

from ..config import settings
from ..models import Article, FetchLog
from ..time_utils import beijing_now

GMAIL_API = "https://gmail.googleapis.com/gmail/v1/users/me"


def _gmail_get(path: str, params: dict = None) -> dict:
    """Authenticated GET to Gmail REST API via proxy."""
    proxies = {"http": settings.http_proxy, "https": settings.http_proxy} if settings.http_proxy else None
    headers = {"Authorization": f"Bearer {_get_access_token()}"}
    resp = http.get(f"{GMAIL_API}/{path}", headers=headers, params=params,
                    proxies=proxies, timeout=30)
    resp.raise_for_status()
    return resp.json()


def _get_access_token() -> str:
    """Get OAuth access token via proxy."""
    proxies = {"http": settings.http_proxy, "https": settings.http_proxy} if settings.http_proxy else None
    resp = http.post("https://oauth2.googleapis.com/token", data={
        "client_id": settings.gmail_client_id,
        "client_secret": settings.gmail_client_secret,
        "refresh_token": settings.gmail_refresh_token,
        "grant_type": "refresh_token",
    }, proxies=proxies, timeout=15)
    resp.raise_for_status()
    return resp.json()["access_token"]


def test_gmail_connection(email_addr: str) -> tuple[bool, str]:
    """Test Gmail API connectivity."""
    if not settings.gmail_client_id or not settings.gmail_refresh_token:
        return False, "Gmail OAuth 未配置"
    try:
        profile = _gmail_get("profile")
        return True, f"Gmail API 连接成功: {profile.get('emailAddress', '')}"
    except Exception as e:
        return False, f"Gmail API 连接失败: {e}"


def fetch_gmail_articles(email_addr: str, db_session) -> int:
    """Fetch newsletter emails from Gmail, parse Medium/InfoQ article links."""
    if not settings.gmail_client_id or not settings.gmail_refresh_token:
        return 0

    try:
        after_date = (beijing_now() - timedelta(days=3)).strftime("%Y/%m/%d")
        result = _gmail_get("messages", {"q": f"after:{after_date}", "maxResults": 20})
    except Exception:
        return 0

    messages = result.get("messages", [])
    if not messages:
        return 0

    existing_urls = {u[0] for u in db_session.query(Article.url).filter(Article.url.isnot(None)).all() if u[0]}
    new_count = 0

    for msg_meta in messages:
        try:
            msg = _gmail_get(f"messages/{msg_meta['id']}", {"format": "full"})
        except Exception:
            continue

        headers = {h["name"].lower(): h["value"] for h in msg.get("payload", {}).get("headers", [])}
        subject = _decode(subject=headers.get("subject", ""))
        from_addr = headers.get("from", "")

        if not subject or len(subject) < 2:
            continue

        body_text, links, link_texts = _extract(msg.get("payload", {}))
        source_name = _detect_source(from_addr, subject, body_text)

        date_str = headers.get("date", "")
        pub_date = None
        if date_str:
            try:
                pub_date = parsedate_to_datetime(date_str)
            except Exception:
                pub_date = beijing_now()
        pub_date = pub_date or beijing_now()

        if links and source_name in ("Medium", "InfoQ"):
            article_links = _filter_links(links, source_name)
            for link in article_links[:10]:
                if link in existing_urls:
                    continue
                title = link_texts.get(link, "") if link_texts else ""
                if not title or len(title) < 5:
                    title = _url_to_title(link)
                if not title or len(title) < 5:
                    continue
                db_session.add(Article(
                    title=title[:1024], url=link[:2048],
                    source_type="EMAIL", source_name=source_name,
                    content_preview=body_text[:500], full_content=body_text,
                    publish_date=pub_date, fetched_at=beijing_now(),
                    domains=[], tags=[], format="行业动态", relevance_score=0,
                ))
                existing_urls.add(link)
                new_count += 1
        else:
            url = links[0] if links else f"https://mail.google.com/mail/u/0/#inbox/{msg_meta['id']}"
            if url not in existing_urls:
                db_session.add(Article(
                    title=subject[:1024], url=url[:2048],
                    source_type="EMAIL", source_name=source_name,
                    content_preview=body_text[:500], full_content=body_text,
                    publish_date=pub_date, fetched_at=beijing_now(),
                    domains=[], tags=[], format="行业动态", relevance_score=0,
                ))
                existing_urls.add(url)
                new_count += 1

    if new_count > 0:
        db_session.add(FetchLog(
            source_type="EMAIL", source_name=f"Gmail ({email_addr})",
            articles_found=len(messages), articles_new=new_count,
            fetched_at=beijing_now(),
        ))

    return new_count


def _filter_links(links: list, source: str) -> list:
    kept = []
    for l in links:
        if not l.startswith("http"):
            continue
        low = l.lower()
        if any(x in low for x in ["unsubscribe", "etrack01.com", "itunes.apple.com",
                                    "play.google.com", "mailto:"]):
            continue
        if source == "Medium" and not _is_medium_article(l):
            continue
        kept.append(l)
    seen = set()
    unique = []
    for l in kept:
        base = l.split("?source=")[0].split("?utm_")[0]
        if base not in seen:
            seen.add(base)
            unique.append(l)
    return unique


def _is_medium_article(url: str) -> bool:
    path = url.split("medium.com/")[-1] if "medium.com/" in url else ""
    if not path or path.startswith("?"):
        return False
    parts = path.split("/")
    if len(parts) < 2:
        return False
    slug = parts[-1].split("?")[0]
    return bool(re.search(r"-[a-f0-9]{8,}$", slug))


def _url_to_title(url: str) -> str:
    parts = url.rstrip("/").split("/")
    for p in reversed(parts):
        if len(p) > 10 and "-" in p and not p.startswith("?"):
            return p.replace("-", " ").title()[:200]
    return ""


def _detect_source(from_addr: str, subject: str, body: str = "") -> str:
    combined = (from_addr + " " + subject + " " + body[:500]).lower()
    if "medium" in combined or "noreply@medium" in combined:
        return "Medium"
    if "infoq" in combined:
        return "InfoQ"
    if "coindesk" in combined:
        return "CoinDesk"
    if "hackernews" in combined or "hacker news" in combined:
        return "Hacker News"
    if "cointelegraph" in combined:
        return "CoinTelegraph"
    m = re.search(r"@([\w.]+)", from_addr)
    return m.group(1).split(".")[0].title() if m else "Email"


def _extract(payload: dict) -> tuple:
    body, links, link_texts, html_body = "", [], {}, ""

    def walk(part):
        nonlocal body, html_body, links, link_texts
        mime = part.get("mimeType", "")
        data = part.get("body", {}).get("data", "")
        if data:
            try:
                decoded = base64.urlsafe_b64decode(data + "===").decode("utf-8", errors="replace")
            except Exception:
                decoded = data
            if mime == "text/html" and not html_body:
                html_body = decoded
                soup = BeautifulSoup(decoded, "lxml")
                for a in soup.find_all("a", href=True):
                    href, text = a["href"], a.get_text(strip=True)
                    if href.startswith("http"):
                        links.append(href)
                        if text and len(text) > 5:
                            link_texts[href] = text
                body = soup.get_text(separator="\n", strip=True)
            elif mime == "text/plain" and not body:
                body = decoded
        for sub in part.get("parts", []):
            walk(sub)

    walk(payload)
    lines = [l.strip() for l in body.split("\n") if l.strip()]
    return "\n".join(lines[:30]), links, link_texts


def _decode(**values) -> str:
    subject = values.get("subject", "")
    if not subject:
        return "(无标题)"
    parts = decode_header(subject)
    result = []
    for part, charset in parts:
        if isinstance(part, bytes):
            try:
                result.append(part.decode(charset or "utf-8", errors="replace"))
            except Exception:
                result.append(part.decode("utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result).strip()
