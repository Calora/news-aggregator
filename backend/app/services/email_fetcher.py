"""IMAP email fetcher for QQ, 163, and other providers."""
import email
import imaplib
import ssl
from datetime import datetime, timedelta
from ..time_utils import beijing_now
from email.header import decode_header
from bs4 import BeautifulSoup

from ..models import EmailAccount, Article, FetchLog
from ..routers.sources import _decrypt


def test_connection(email_addr: str, auth_code: str, server: str, port: int) -> tuple[bool, str]:
    try:
        ctx = ssl.create_default_context()
        with imaplib.IMAP4_SSL(server, port, ssl_context=ctx) as conn:
            conn.login(email_addr, auth_code)
            result, data = conn.select("INBOX")
            if result != "OK":
                msg = data[0].decode() if isinstance(data[0], bytes) else str(data[0])
                msg_short = msg[:120]
                if "unsafe" in msg.lower() or "unsafe" in msg:
                    return False, f"163安全限制: 请在163邮箱网页版→设置→POP3/SMTP/IMAP→开启'允许第三方客户端'。详情: {msg_short}"
                return False, f"无法打开收件箱: {msg_short}"
            return True, "连接成功"
    except imaplib.IMAP4.error as e:
        return False, f"IMAP错误: {e}"
    except Exception as e:
        return False, f"连接失败: {e}"


def fetch_all_emails(db_session) -> int:
    accounts = db_session.query(EmailAccount).filter(EmailAccount.enabled == True).all()
    total_new = 0
    for acc in accounts:
        try:
            # Gmail accounts use official API (HTTPS), others use IMAP
            if "gmail" in acc.email.lower():
                try:
                    from .gmail_fetcher import fetch_gmail_articles
                    new_count = fetch_gmail_articles(acc.email, db_session)
                except Exception as e:
                    print(f"Gmail fetch failed (non-fatal): {e}")
                    new_count = 0
            else:
                new_count = _fetch_account(acc, db_session)
            total_new += new_count
            acc.last_fetch_at = beijing_now()
        except Exception as e:
            db_session.add(FetchLog(
                source_type="EMAIL",
                source_name=acc.email,
                articles_found=0,
                articles_new=0,
                fetched_at=beijing_now(),
            ))
    db_session.commit()
    return total_new


def _fetch_account(acc: EmailAccount, db_session) -> int:
    auth_code = _decrypt(acc.auth_code_encrypted)
    ctx = ssl.create_default_context()

    with imaplib.IMAP4_SSL(acc.imap_server, acc.imap_port, ssl_context=ctx) as conn:
        conn.login(acc.email, auth_code)
        result, sel_data = conn.select("INBOX")
        if result != "OK":
            raise Exception(f"SELECT INBOX failed: {sel_data}")

        since = (beijing_now() - timedelta(days=2)).strftime("%d-%b-%Y")
        status, messages = conn.search(None, f'(SINCE "{since}")')

        if status != "OK":
            return 0

        msg_ids = messages[0].split()
        found = len(msg_ids)
        new_count = 0

        existing_urls = set()
        for msg_id in msg_ids[-100:]:
            status, data = conn.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            raw = data[0][1]
            msg = email.message_from_bytes(raw)

            subject = _decode_header(msg["Subject"] or "")
            body_text, links = _extract_body(msg)
            article_url = links[0] if links else None

            if article_url and article_url in existing_urls:
                continue

            # Title-based dedup check
            from .deduplicator import is_duplicate
            if is_duplicate(subject, article_url or "", db_session):
                continue

            if article_url:
                existing_urls.add(article_url)

            date_str = msg["Date"]
            pub_date = None
            if date_str:
                try:
                    from email.utils import parsedate_to_datetime
                    pub_date = parsedate_to_datetime(date_str)
                except Exception:
                    pub_date = beijing_now()

            article = Article(
                title=subject,
                url=article_url or "",
                source_type="EMAIL",
                source_name=acc.email.split("@")[-1].split(".")[0].upper(),
                content_preview=body_text[:500] if body_text else None,
                full_content=body_text,
                publish_date=pub_date or beijing_now(),
                fetched_at=beijing_now(),
                domains=[],
                tags=[],
                format="行业动态",
                relevance_score=0,
            )
            db_session.add(article)
            new_count += 1

        db_session.add(FetchLog(
            source_type="EMAIL",
            source_name=acc.email,
            articles_found=found,
            articles_new=new_count,
            fetched_at=beijing_now(),
        ))

        return new_count


def _decode_header(value: str) -> str:
    if not value:
        return "(无标题)"
    parts = decode_header(value)
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


def _extract_body(msg) -> tuple[str, list[str]]:
    body = ""
    links = []
    html_body = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            if content_type == "text/html" and not html_body:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body = payload.decode("utf-8", errors="replace")
                except Exception:
                    pass
            elif content_type == "text/plain" and not body:
                try:
                    payload = part.get_payload(decode=True)
                    if payload:
                        body = payload.decode("utf-8", errors="replace")
                except Exception:
                    pass
    else:
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                body = payload.decode("utf-8", errors="replace")
        except Exception:
            pass

    if html_body:
        soup = BeautifulSoup(html_body, "lxml")
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href.startswith("http") and "unsubscribe" not in href.lower():
                links.append(href)
        body = soup.get_text(separator="\n", strip=True)

    lines = [l.strip() for l in body.split("\n") if l.strip()]
    body = "\n".join(lines[:30])

    return body, links
