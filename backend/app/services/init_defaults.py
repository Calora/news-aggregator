"""Initialize default web sources on first run."""
from ..models import WebSource

DEFAULT_RSS_SOURCES = [
    # 用户订阅（邮件替代）
    ("InfoQ", "https://feed.infoq.com/", "RSS"),
    ("Medium - Technology", "https://medium.com/feed/tag/blockchain", "WEB"),
    # Blockchain / Crypto
    ("Ethresear.ch", "https://ethresear.ch/posts.rss", "RSS"),
    ("The Block", "https://www.theblock.co/rss", "RSS"),
    ("Messari", "https://messari.io/feed", "RSS"),
    ("a16z Crypto", "https://a16zcrypto.com/feed/", "RSS"),
    ("CoinTelegraph", "https://cointelegraph.com/rss", "RSS"),
    ("Decrypt", "https://decrypt.co/feed", "RSS"),
    # ZK / Crypto
    ("IACR ePrint", "https://eprint.iacr.org/rss", "RSS"),
    ("ZK Mesh", "https://zkmesh.substack.com/feed", "RSS"),
    ("Zero Knowledge Blog", "https://zeroknowledge.fm/feed", "RSS"),
    # AI / Tech
    ("Hacker News", "https://hnrss.org/frontpage", "RSS"),
    # 政策法规 — 中国政府网 + 部委（优先RSS，无法提供则WEB抓取）
    ("国务院政策", "http://www.gov.cn/rss/", "WEB"),
    ("国家网信办", "https://www.cac.gov.cn/wxzw/A0936index_1.htm", "WEB"),
    ("工信部政策", "https://www.miit.gov.cn/zwgk/zcwj/index.html", "WEB"),
    ("国家数据局", "https://www.ndrc.gov.cn/fzggw/jgsj/sjj/", "WEB"),
    ("中央网络安全和信息化委员会", "http://www.cac.gov.cn/rss/", "WEB"),
]


def ensure_default_sources(db_session):
    existing_urls = {s.url for s in db_session.query(WebSource).all()}
    added = 0
    for name, url, stype in DEFAULT_RSS_SOURCES:
        if url not in existing_urls:
            db_session.add(WebSource(name=name, url=url, source_type=stype))
            added += 1
    if added:
        db_session.commit()
    return added
