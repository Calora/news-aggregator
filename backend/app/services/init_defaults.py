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
    ("Ethereum Foundation Blog", "https://blog.ethereum.org/feed.xml", "RSS"),
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
