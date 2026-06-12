"""Feishu (Lark) API integration — create docs from bookmark groups."""
import requests
import time
from ..config import settings


FEISHU_API = "https://open.feishu.cn/open-apis"
_TOKEN_CACHE = {"token": "", "expires_at": 0}
_NO_PROXY = {"http": "", "https": ""}


def _get_access_token() -> str:
    now = time.time()
    if _TOKEN_CACHE["token"] and _TOKEN_CACHE["expires_at"] > now + 60:
        return _TOKEN_CACHE["token"]

    resp = requests.post(f"{FEISHU_API}/auth/v3/tenant_access_token/internal", json={
        "app_id": settings.feishu_app_id,
        "app_secret": settings.feishu_app_secret,
    }, timeout=10, proxies=_NO_PROXY)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Feishu auth failed: {data}")

    _TOKEN_CACHE["token"] = data["tenant_access_token"]
    _TOKEN_CACHE["expires_at"] = now + data.get("expire", 7200)
    return _TOKEN_CACHE["token"]


def append_to_doc(doc_id: str, blocks: list[dict]) -> dict:
    """Append blocks to an existing document. Returns doc info."""
    token = _get_access_token()

    # Check document exists
    resp = requests.get(f"{FEISHU_API}/docx/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {token}"}, timeout=10, proxies=_NO_PROXY)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Doc not found: {data}")

    # Add blocks in batches (max 50 per call)
    for i in range(0, len(blocks), 50):
        batch = blocks[i:i + 50]
        resp = requests.post(f"{FEISHU_API}/docx/v1/documents/{doc_id}/blocks/{doc_id}/children", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }, json={"children": batch}, timeout=30, proxies=_NO_PROXY)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Feishu append failed (batch {i // 50 + 1}): {data}")

    doc_url = f"https://calosia.feishu.cn/docx/{doc_id}"
    return {"doc_id": doc_id, "url": doc_url}


def create_doc(title: str, blocks: list[dict], folder_token: str = "") -> dict:
    """Create a Feishu Docx document with structured content. Returns doc info."""
    token = _get_access_token()

    # 1. Create empty document
    resp = requests.post(f"{FEISHU_API}/docx/v1/documents", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }, json={"title": title}, timeout=15, proxies=_NO_PROXY)
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Feishu create doc failed: {data}")
    doc_id = data["data"]["document"]["document_id"]

    # 2. Add blocks in batches (max 50 per call)
    for i in range(0, len(blocks), 50):
        batch = blocks[i:i + 50]
        resp = requests.post(f"{FEISHU_API}/docx/v1/documents/{doc_id}/blocks/{doc_id}/children", headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }, json={"children": batch}, timeout=30, proxies=_NO_PROXY)
        data = resp.json()
        if data.get("code") != 0:
            raise Exception(f"Feishu add blocks failed (batch {i // 50 + 1}): {data}")

    doc_url = f"https://calosia.feishu.cn/docx/{doc_id}"
    return {"doc_id": doc_id, "url": doc_url, "title": title}


# ── Block builders ───────────────────────────────────────────────

def _h1(content: str) -> dict:
    return {"block_type": 3, "heading1": {"elements": [{"text_run": {"content": content}}], "style": {}}}

def _h2(content: str) -> dict:
    return {"block_type": 4, "heading2": {"elements": [{"text_run": {"content": content}}], "style": {}}}

def _p(content: str) -> dict:
    return {"block_type": 2, "text": {"elements": [{"text_run": {"content": content}}], "style": {}}}

def _rich(elements: list[dict]) -> dict:
    """Text block with rich elements (bold, links, etc)."""
    return {"block_type": 2, "text": {"elements": elements, "style": {}}}

def _empty() -> dict:
    return {"block_type": 2, "text": {"elements": [{"text_run": {"content": ""}}], "style": {}}}


def build_doc_blocks(group: dict) -> list[dict]:
    """Convert a bookmark group into Feishu document blocks."""
    blocks = [_h1("写作素材")]

    for i, article in enumerate(group["articles"], 1):
        title = article.get("title", "无标题")
        url = article.get("url", "")
        summary = article.get("summary_cn") or (article.get("content_preview") or "")[:200]
        score = article.get("relevance_score", 0)
        reason = article.get("reason", "")

        blocks.append(_h2(f"素材 {i}：{title}"))

        if url:
            blocks.append(_rich([
                {"text_run": {"content": "链接：", "text_element_style": {"bold": True}}},
                {"text_run": {"content": url, "text_element_style": {"link": {"url": url}}}},
            ]))

        if summary:
            blocks.append(_p(f"摘要：{summary}"))

        meta = f"评分：★{score}"
        if reason:
            meta += f"　｜　{reason}"
        blocks.append(_p(meta))
        blocks.append(_empty())

    # Section break
    blocks.append(_p("━" * 20))
    blocks.append(_h1("推荐公众号标题"))

    for j, t in enumerate(group.get("suggested_titles", []), 1):
        blocks.append(_p(f"{j}. {t}"))

    return blocks


def clear_doc(doc_id: str, keep_title: bool = True) -> bool:
    """Remove all child blocks from a document. Returns True on success."""
    token = _get_access_token()
    # Get all children
    resp = requests.get(f"{FEISHU_API}/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
        headers={"Authorization": f"Bearer {token}"}, timeout=10, proxies=_NO_PROXY)
    data = resp.json()
    if data.get("code") != 0:
        return False

    items = data["data"].get("items", [])
    if not items:
        return True

    # Delete each child block
    for item in items:
        bid = item["block_id"]
        requests.delete(f"{FEISHU_API}/docx/v1/documents/{doc_id}/blocks/{bid}",
            headers={"Authorization": f"Bearer {token}"}, timeout=10, proxies=_NO_PROXY)
    return True


def test_connection() -> tuple[bool, str]:
    try:
        token = _get_access_token()
        return True, f"飞书连接成功 (token: {token[:10]}...)"
    except Exception as e:
        return False, f"飞书连接失败: {e}"
