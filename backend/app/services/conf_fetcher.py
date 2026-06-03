"""CCF-A conference paper tracking via DBLP API."""
import re
from datetime import datetime

import httpx
from ..time_utils import beijing_now

from ..models import Article, FetchLog

# CCF-A conferences relevant to blockchain/ZK/AI/SE
CCF_A_VENUES = [
    # Security
    ("CCS", "ACM CCS", "conf/ccs"),
    ("S&P", "IEEE S&P", "conf/sp"),
    ("USENIX Security", "USENIX Security", "conf/uss"),
    ("NDSS", "NDSS", "conf/ndss"),
    # Cryptography
    ("CRYPTO", "CRYPTO", "conf/crypto"),
    ("EUROCRYPT", "EUROCRYPT", "conf/eurocrypt"),
    ("ASIACRYPT", "ASIACRYPT", "conf/asiacrypt"),
    # Software Engineering
    ("ICSE", "ICSE", "conf/icse"),
    ("FSE", "FSE", "conf/sigsoft"),
    ("ASE", "ASE", "conf/kbse"),
    # AI/ML (filter for blockchain/ZK-related only)
    ("NeurIPS", "NeurIPS", "conf/nips"),
    ("ICML", "ICML", "conf/icml"),
    ("AAAI", "AAAI", "conf/aaai"),
    # Systems
    ("OSDI", "OSDI", "conf/osdi"),
    ("SOSP", "SOSP", "conf/sosp"),
]

ZK_BC_KEYWORDS = [
    "zero-knowledge", "zero knowledge", "zk", "zkSNARK", "zkSTARK",
    "plonky", "halo2", "gnark", "circom", "snarkjs",
    "NTT", "MSM", "polynomial commitment", "proof system",
    "verifiable computation", "folding scheme", "lookup table",
    "gpu", "fpga", "asic", "hardware accel",
    "recursive proof", "homomorphic", "MPC", "multi-party", "fhe",
    "blockchain", "ethereum", "solana", "consensus",
    "smart contract", "solidity", "layer 2", "rollup",
    "cross-chain", "bridge", "byzantine",
    "sharding", "MEV", "validator", "staking",
    "distributed ledger", "formal verification",
]


def fetch_all_conf_papers(db_session) -> int:
    """Fetch recent papers from CCF-A conferences via DBLP."""
    current_year = beijing_now().year
    total_new = 0

    for acronym, full_name, dblp_path in CCF_A_VENUES:
        for year in [current_year, current_year - 1]:
            try:
                new_count = _fetch_venue(acronym, full_name, dblp_path, year, db_session)
                total_new += new_count
            except Exception:
                pass

    db_session.commit()
    return total_new


def _fetch_venue(acronym: str, full_name: str, dblp_path: str, year: int, db_session) -> int:
    """Fetch papers from a specific conference venue + year."""
    # Try multiple DBLP query strategies
    queries = [
        f"https://dblp.org/search/publ/api?q=toc%3Adb%2F{dblp_path}{year}.bht%3A&format=json&h=30",
        f"https://dblp.org/search/publ/api?q=venue%3A{acronym.replace(' ', '_')}%20year%3A{year}&format=json&h=30",
        f"https://dblp.org/search/publ/api?q={full_name.replace(' ', '_')}%20year%3A{year}&format=json&h=30",
    ]

    data = None
    for url in queries:
        try:
            resp = httpx.get(url, timeout=20, headers={"User-Agent": "NewsDigest/1.0"})
            resp.raise_for_status()
            data = resp.json()
            hits = data.get("result", {}).get("hits", {}).get("hit", [])
            total = int(data.get("result", {}).get("hits", {}).get("@total", 0))
            if total > 0:
                break
        except Exception:
            continue

    if not data:
        return 0

    hits = data.get("result", {}).get("hits", {}).get("hit", [])
    if not isinstance(hits, list):
        hits = [hits] if hits else []

    existing_titles = {t[0].lower().strip() for t in db_session.query(Article.title).all()}
    new_count = 0

    for hit in hits:
        info = hit.get("info", {})
        title = info.get("title", "").strip()
        if not title or len(title) < 10:
            continue

        title_lower = title.lower()
        if title_lower in existing_titles:
            continue

        # For AI/ML conferences, filter to only blockchain/ZK related papers
        ai_venues = ["NeurIPS", "ICML", "AAAI"]
        if acronym in ai_venues:
            combined = title_lower + " " + (info.get("abstract", "") or "").lower()
            if not any(kw in combined for kw in ZK_BC_KEYWORDS):
                continue

        authors_list = info.get("authors", {}).get("author", [])
        if isinstance(authors_list, dict):
            authors_list = [authors_list]
        authors = ", ".join(
            a.get("text", a) if isinstance(a, dict) else str(a)
            for a in authors_list[:5]
        )

        doi = info.get("doi", "")
        ee = info.get("ee", "")
        paper_url = doi or ee or f"https://dblp.org/rec/{hit.get('@id', '')}"

        pub_date = datetime(year, 7, 1)  # Approximate conference date

        article = Article(
            title=title[:1024],
            url=str(paper_url)[:2048],
            source_type="CONF",
            source_name=f"{acronym} {year}",
            content_preview=info.get("abstract", info.get("bibtex", ""))[:500],
            full_content=info.get("abstract", ""),
            authors=authors,
            publish_date=pub_date,
            fetched_at=beijing_now(),
            domains=[],
            tags=[],
            format="学术论文",
            relevance_score=9,  # CCF-A papers start at 9
        )
        db_session.add(article)
        new_count += 1
        existing_titles.add(title_lower)

    if new_count > 0:
        db_session.add(FetchLog(
            source_type="CONF",
            source_name=f"{acronym} {year}",
            articles_found=len(hits),
            articles_new=new_count,
            fetched_at=beijing_now(),
        ))

    return new_count
