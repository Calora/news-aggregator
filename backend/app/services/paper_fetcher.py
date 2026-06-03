"""Academic paper tracking: arXiv API for blockchain/ZK related papers."""
import re
from datetime import datetime

import arxiv
from ..time_utils import beijing_now

from ..models import Article, FetchLog

TOPICS = [
    ("cs.CR", "Cryptography and Security"),
    ("cs.DC", "Distributed, Parallel, and Cluster Computing"),
    ("cs.AI", "Artificial Intelligence"),
    ("cs.LG", "Machine Learning"),
]

CONFERENCE_NAMES = [
    "ACM CCS", "IEEE S&P", "USENIX Security", "NDSS",
    "CRYPTO", "EUROCRYPT", "ASIACRYPT", "CHES",
    "ICSE", "FSE", "ESEC", "ASE",
]

ZK_KEYWORDS = [
    "zero-knowledge", "zero knowledge", "zk", "zkSNARK", "zkSTARK", "zkp",
    "plonky", "halo2", "gnark", "circom", "snarkjs",
    "NTT", "MSM", "polynomial commitment", "polynomial",
    "folding scheme", "lookup table", "proof system",
    "verifiable computation", "verifiable delay",
    "gpu", "fpga", "asic", "hardware accelerat",
    "recursive proof", "incrementally verifiable",
    "witness encryption", "homomorphic", "MPC", "multi-party",
    "fhe", "fully homomorphic",
]

BLOCKCHAIN_KEYWORDS = [
    "blockchain", "ethereum", "solana", "consensus",
    "smart contract", "solidity", "layer 2", "rollup",
    "cross-chain", "bridge", "DAG", "byzantine",
    "sharding", "danksharding", "MEV", "PBS",
    "validator", "staking", "proof of stake",
    "distributed ledger", "permissioned",
]


def fetch_all_papers(db_session) -> int:
    total_new = 0
    for cat, _ in TOPICS:
        try:
            new_count = _fetch_arxiv_category(cat, db_session)
            total_new += new_count
        except Exception:
            pass
    db_session.commit()
    return total_new


def _fetch_arxiv_category(category: str, db_session) -> int:
    """Fetch recent papers from arXiv category, pre-filter by relevance."""
    search = arxiv.Search(
        query=f"cat:{category}",
        max_results=20,
        sort_by=arxiv.SortCriterion.SubmittedDate,
    )

    existing_titles = {t[0].lower().strip() for t in db_session.query(Article.title).all()}
    new_count = 0

    try:
        for result in search.results():
            title = result.title.strip()
            title_lower = title.lower()
            summary = result.summary.replace("\n", " ").strip()
            summary_lower = summary.lower()
            combined = title_lower + " " + summary_lower

            if title_lower in existing_titles:
                continue

            # Check relevance: only keep papers related to ZK/crypto acceleration or blockchain
            is_zk = any(kw.lower() in combined for kw in ZK_KEYWORDS)
            is_bc = any(kw.lower() in combined for kw in BLOCKCHAIN_KEYWORDS)
            is_conf = any(conf.lower() in combined for conf in CONFERENCE_NAMES)

            if not (is_zk or is_bc or is_conf):
                continue

            authors = ", ".join(a.name for a in result.authors[:5])

            article = Article(
                title=title[:1024],
                url=result.entry_id,
                source_type="ARXIV",
                source_name=f"arXiv {category}",
                content_preview=summary[:500],
                full_content=summary,
                authors=authors,
                publish_date=result.published or beijing_now(),
                fetched_at=beijing_now(),
                domains=[],
                tags=_extract_paper_tags(title_lower + " " + summary_lower),
                format="学术论文",
                relevance_score=0,
            )
            db_session.add(article)
            new_count += 1

        db_session.add(FetchLog(
            source_type="ARXIV", source_name=f"arXiv {category}",
            articles_found=new_count, articles_new=new_count,
            fetched_at=beijing_now(),
        ))
    except Exception:
        pass

    return new_count


def _extract_paper_tags(text: str) -> list[str]:
    tags = []
    tag_map = {
        "GPU加速": ["gpu", "nvidia", "cuda"],
        "NTT": ["ntt", "number theoretic transform"],
        "MSM": ["msm", "multi-scalar multiplication"],
        "零知识证明": ["zero-knowledge", "zero knowledge", "zkp", "zksnark", "zkstark"],
        "递归证明": ["recursive proof", "incrementally verifiable"],
        "多项式承诺": ["polynomial commitment"],
        "查找表": ["lookup table", "lookup argument"],
        "全同态加密": ["fhe", "fully homomorphic", "homomorphic encryption"],
        "多方安全计算": ["mpc", "multi-party", "secure multi-party"],
        "zkEVM": ["zkevm"],
        "zkRollup": ["zkrollup", "zk rollup"],
        "以太坊": ["ethereum"],
        "Rollup": ["rollup"],
        "共识机制": ["consensus", "byzantine"],
        "智能合约": ["smart contract", "solidity"],
        "跨链": ["cross-chain", "bridge", "interoperability"],
        "形式化验证": ["formal verification"],
        "后量子密码": ["post-quantum", "pqc", "lattice-based"],
    }
    for tag, keywords in tag_map.items():
        if any(kw in text for kw in keywords):
            tags.append(tag)
    return tags[:5]
