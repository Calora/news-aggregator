from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import EmailAccount, WebSource, FetchLog
from ..schemas import EmailAccountCreate, EmailAccountUpdate, WebSourceCreate, WebSourceUpdate

router = APIRouter()

# ── Email Accounts ──────────────────────────────────────────────

@router.get("/sources/email")
def list_email_accounts(db: Session = Depends(get_db)):
    return [a.to_dict() for a in db.query(EmailAccount).all()]


@router.post("/sources/email")
def create_email_account(data: EmailAccountCreate, db: Session = Depends(get_db)):
    existing = db.query(EmailAccount).filter(EmailAccount.email == data.email).first()
    if existing:
        # Update existing
        existing.auth_code_encrypted = _encrypt(data.auth_code)
        existing.imap_server = data.imap_server
        existing.imap_port = data.imap_port
        existing.enabled = True
    else:
        acc = EmailAccount(
            email=data.email,
            auth_code_encrypted=_encrypt(data.auth_code),
            imap_server=data.imap_server,
            imap_port=data.imap_port,
        )
        db.add(acc)
    db.commit()
    acc = db.query(EmailAccount).filter(EmailAccount.email == data.email).first()
    return acc.to_dict() if acc else {}


@router.put("/sources/email/{acc_id}")
def update_email_account(acc_id: int, data: EmailAccountUpdate, db: Session = Depends(get_db)):
    acc = db.query(EmailAccount).filter(EmailAccount.id == acc_id).first()
    if not acc:
        return {"error": "not found"}
    if data.email is not None:
        acc.email = data.email
    if data.auth_code is not None:
        acc.auth_code_encrypted = _encrypt(data.auth_code)
    if data.imap_server is not None:
        acc.imap_server = data.imap_server
    if data.imap_port is not None:
        acc.imap_port = data.imap_port
    if data.enabled is not None:
        acc.enabled = data.enabled
    db.commit()
    return acc.to_dict()


@router.delete("/sources/email/{acc_id}")
def delete_email_account(acc_id: int, db: Session = Depends(get_db)):
    acc = db.query(EmailAccount).filter(EmailAccount.id == acc_id).first()
    if acc:
        db.delete(acc)
        db.commit()
    return {"ok": True}


@router.post("/sources/email/{acc_id}/test")
def test_email_account(acc_id: int, db: Session = Depends(get_db)):
    acc = db.query(EmailAccount).filter(EmailAccount.id == acc_id).first()
    if not acc:
        return {"ok": False, "message": "账号不存在"}
    try:
        if "gmail" in acc.email.lower():
            from ..services.gmail_fetcher import test_gmail_connection
            ok, msg = test_gmail_connection(acc.email)
        else:
            from ..services.email_fetcher import test_connection
            ok, msg = test_connection(acc.email, _decrypt(acc.auth_code_encrypted),
                                       acc.imap_server, acc.imap_port)
        return {"ok": ok, "message": msg}
    except Exception as e:
        return {"ok": False, "message": str(e)}


# ── Web Sources ──────────────────────────────────────────────────

@router.get("/sources/web")
def list_web_sources(db: Session = Depends(get_db)):
    return [s.to_dict() for s in db.query(WebSource).all()]


@router.post("/sources/web")
def create_web_source(data: WebSourceCreate, db: Session = Depends(get_db)):
    existing = db.query(WebSource).filter(WebSource.url == data.url).first()
    if existing:
        existing.name = data.name
        existing.source_type = data.source_type
        existing.enabled = True
    else:
        src = WebSource(name=data.name, url=data.url, source_type=data.source_type)
        db.add(src)
    db.commit()
    src = db.query(WebSource).filter(WebSource.url == data.url).first()
    return src.to_dict() if src else {}


@router.put("/sources/web/{src_id}")
def update_web_source(src_id: int, data: WebSourceUpdate, db: Session = Depends(get_db)):
    src = db.query(WebSource).filter(WebSource.id == src_id).first()
    if not src:
        return {"error": "not found"}
    if data.name is not None:
        src.name = data.name
    if data.url is not None:
        src.url = data.url
    if data.source_type is not None:
        src.source_type = data.source_type
    if data.enabled is not None:
        src.enabled = data.enabled
    db.commit()
    return src.to_dict()


@router.delete("/sources/web/{src_id}")
def delete_web_source(src_id: int, db: Session = Depends(get_db)):
    src = db.query(WebSource).filter(WebSource.id == src_id).first()
    if src:
        db.delete(src)
        db.commit()
    return {"ok": True}


@router.post("/sources/web/test")
def test_web_source(data: dict, db: Session = Depends(get_db)):
    """Test if a web source URL is reachable."""
    import requests
    url = data.get("url", "")
    if not url:
        return {"ok": False, "message": "URL 不能为空"}
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "NewsDigest/1.0"})
        if resp.status_code < 400:
            return {"ok": True, "message": f"连接成功 (HTTP {resp.status_code}, {len(resp.content)} bytes)"}
        else:
            return {"ok": False, "message": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"ok": False, "message": f"连接失败: {str(e)[:100]}"}


# ── Fetch Logs ───────────────────────────────────────────────────

@router.get("/fetch/logs")
def get_fetch_logs(limit: int = 20, db: Session = Depends(get_db)):
    logs = db.query(FetchLog).order_by(FetchLog.fetched_at.desc()).limit(limit).all()
    return [log.to_dict() for log in logs]


@router.post("/fetch")
def trigger_fetch(db: Session = Depends(get_db)):
    from ..services.email_fetcher import fetch_all_emails
    from ..services.web_fetcher import fetch_all_web
    from ..services.classifier import process_unclassified

    from ..services.deduplicator import cleanup_duplicates

    email_new = fetch_all_emails(db)
    web_new = fetch_all_web(db)
    processed = process_unclassified(db)
    dedup_removed = cleanup_duplicates(db)

    return {
        "ok": True,
        "message": f"邮件 {email_new}, RSS/Web {web_new} 条新增, AI 处理 {processed} 条, 去重 {dedup_removed} 条",
    }


@router.post("/dedup")
def dedup_articles(db: Session = Depends(get_db)):
    from ..services.deduplicator import cleanup_duplicates
    from ..models import Article
    removed = cleanup_duplicates(db)
    total = db.query(Article).count()
    return {"ok": True, "message": f"清理完成: 删除 {removed} 条重复, 剩余 {total} 条"}


@router.post("/reprocess")
def reprocess_all(db: Session = Depends(get_db)):
    """Re-run AI pipeline on ALL unprocessed (score=0) articles, in batches."""
    from ..services.classifier import process_unclassified
    from ..models import Article

    total = db.query(Article).filter(Article.relevance_score == 0).count()
    processed_total = 0

    # Process in batches of 20 until done or max 200
    for _ in range(10):
        n = process_unclassified(db)
        if n == 0:
            break
        processed_total += n

    remaining = db.query(Article).filter(Article.relevance_score == 0).count()
    return {
        "ok": True,
        "message": f"AI 处理完成: 本次处理 {processed_total} 条, 共 {total} 条待处理, 剩余 {remaining} 条",
    }


# ── Helpers ──────────────────────────────────────────────────────

def _encrypt(value: str) -> str:
    from cryptography.fernet import Fernet
    from ..config import settings
    key = settings.deepseek_api_key or "dev-key-32-bytes-padding!!"
    key = (key * 2)[:32].encode()
    import base64
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.encrypt(value.encode()).decode()


def _decrypt(value: str) -> str:
    from cryptography.fernet import Fernet
    from ..config import settings
    key = settings.deepseek_api_key or "dev-key-32-bytes-padding!!"
    key = (key * 2)[:32].encode()
    import base64
    f = Fernet(base64.urlsafe_b64encode(key))
    return f.decrypt(value.encode()).decode()
