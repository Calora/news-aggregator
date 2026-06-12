"""Feishu (Lark) API integration — create docs from bookmark groups."""
import requests
import time
from ..config import settings


FEISHU_API = "https://open.feishu.cn/open-apis"
_TOKEN_CACHE = {"token": "", "expires_at": 0}
# Feishu is accessible in China, bypass proxy
_NO_PROXY = {"http": "", "https": ""}


def _get_access_token() -> str:
    now = time.time()
    if _TOKEN_CACHE["token"] and _TOKEN_CACHE["expires_at"] > now + 60:
        return _TOKEN_CACHE["token"]

    resp = requests.post(f"{FEISHU_API}/auth/v3/tenant_access_token/internal", json={
        "app_id": settings.feishu_app_id,
        "app_secret": settings.feishu_app_secret,
    }, timeout=10, proxies={"http": "", "https": ""})
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Feishu auth failed: {data}")

    _TOKEN_CACHE["token"] = data["tenant_access_token"]
    _TOKEN_CACHE["expires_at"] = now + data.get("expire", 7200)
    return _TOKEN_CACHE["token"]


def create_doc(title: str, content_blocks: list[dict], folder_token: str = "") -> dict:
    """Create a Feishu Docx document with structured content. Returns doc info."""
    token = _get_access_token()

    # 1. Create empty document
    resp = requests.post(f"{FEISHU_API}/docx/v1/documents", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }, json={"title": title}, timeout=15, proxies={"http": "", "https": ""})
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Feishu create doc failed: {data}")
    doc_id = data["data"]["document"]["document_id"]

    # 2. Append content blocks
    resp = requests.post(f"{FEISHU_API}/docx/v1/documents/{doc_id}/blocks/batch_create", headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }, json={"children": content_blocks}, timeout=15, proxies={"http": "", "https": ""})
    data = resp.json()
    if data.get("code") != 0:
        raise Exception(f"Feishu batch create blocks failed: {data}")

    doc_url = f"https://calosia.feishu.cn/docx/{doc_id}"
    return {"doc_id": doc_id, "url": doc_url, "title": title}


def build_doc_blocks(group: dict) -> list[dict]:
    """Convert a bookmark group into Feishu document blocks."""
    blocks = []

    # Section header
    blocks.append({
        "block_id": _bid(),
        "block_type": "text",
        "text": {
            "elements": [
                {"text_run": {"content": "写作素材"}}
            ],
            "style": {"heading_level": 1}
        }
    })

    for i, article in enumerate(group["articles"], 1):
        title = article.get("title", "无标题")
        url = article.get("url", "")
        summary = article.get("summary_cn", article.get("content_preview", "")[:200])
        score = article.get("relevance_score", 0)
        reason = article.get("reason", "")

        # Material subtitle
        blocks.append({
            "block_id": _bid(),
            "block_type": "text",
            "text": {
                "elements": [
                    {"text_run": {"content": f"素材 {i}：{title}", "text_element_style": {"bold": True}}},
                ],
                "style": {"heading_level": 2}
            }
        })

        # URL
        if url:
            blocks.append({
                "block_id": _bid(),
                "block_type": "text",
                "text": {
                    "elements": [
                        {"text_run": {"content": "链接：", "text_element_style": {"bold": True}}},
                        {"text_run": {"content": url, "text_element_style": {"link": {"url": url}}}},
                    ]
                }
            })

        # Summary
        if summary:
            blocks.append({
                "block_id": _bid(),
                "block_type": "text",
                "text": {
                    "elements": [
                        {"text_run": {"content": f"摘要：{summary}"}},
                    ]
                }
            })

        # Score + reason
        meta = f"评分：★{score}"
        if reason:
            meta += f"　｜　{reason}"
        blocks.append({
            "block_id": _bid(),
            "block_type": "text",
            "text": {"elements": [{"text_run": {"content": meta}}]}
        })

        # Divider between articles
        blocks.append({
            "block_id": _bid(),
            "block_type": "text",
            "text": {"elements": [{"text_run": {"content": ""}}]}
        })

    # Suggested titles section
    blocks.append({
        "block_id": _bid(),
        "block_type": "divider",
    })
    blocks.append({
        "block_id": _bid(),
        "block_type": "text",
        "text": {
            "elements": [
                {"text_run": {"content": "推荐公众号标题", "text_element_style": {"bold": True}}},
            ],
            "style": {"heading_level": 1}
        }
    })

    for j, t in enumerate(group.get("suggested_titles", []), 1):
        blocks.append({
            "block_id": _bid(),
            "block_type": "text",
            "text": {
                "elements": [
                    {"text_run": {"content": f"{j}. {t}"}},
                ]
            }
        })

    return blocks


def test_connection() -> tuple[bool, str]:
    try:
        token = _get_access_token()
        return True, f"飞书连接成功 (token: {token[:10]}...)"
    except Exception as e:
        return False, f"飞书连接失败: {e}"


_bid_counter = 0


def _bid() -> str:
    global _bid_counter
    _bid_counter += 1
    return f"block_{_bid_counter}_{int(time.time() * 1000)}"
