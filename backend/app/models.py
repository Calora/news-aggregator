import json
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, Date, JSON
from .database import Base


class EmailAccount(Base):
    __tablename__ = "email_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(256), unique=True, nullable=False)
    auth_code_encrypted = Column(String(512), nullable=False)
    imap_server = Column(String(256), nullable=False)
    imap_port = Column(Integer, nullable=False, default=993)
    enabled = Column(Boolean, default=True)
    last_fetch_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "imap_server": self.imap_server,
            "imap_port": self.imap_port,
            "enabled": self.enabled,
            "last_fetch_at": self.last_fetch_at.isoformat() if self.last_fetch_at else None,
        }


class WebSource(Base):
    __tablename__ = "web_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), nullable=False)
    url = Column(String(1024), nullable=False)
    source_type = Column(String(32), nullable=False, default="RSS")  # RSS, WEB, ARXIV
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "source_type": self.source_type,
            "enabled": self.enabled,
        }


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(1024), nullable=False)
    url = Column(String(2048), nullable=True)
    source_type = Column(String(32), nullable=False)  # EMAIL, RSS, WEB, ARXIV
    source_name = Column(String(256), nullable=False)
    content_preview = Column(Text, nullable=True)
    full_content = Column(Text, nullable=True)
    authors = Column(String(1024), nullable=True)
    publish_date = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    # 三维分类
    domains = Column(JSON, nullable=False, default=list)
    tags = Column(JSON, nullable=False, default=list)
    format = Column(String(32), nullable=False, default="行业动态")

    relevance_score = Column(Integer, nullable=False, default=0)
    summary_cn = Column(String(512), nullable=True)
    reason = Column(String(128), nullable=True)
    is_daily_pick = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "content_preview": self.content_preview,
            "authors": self.authors,
            "publish_date": self.publish_date.isoformat() if self.publish_date else None,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "domains": self.domains or [],
            "tags": self.tags or [],
            "format": self.format,
            "relevance_score": self.relevance_score,
            "summary_cn": self.summary_cn,
            "reason": self.reason,
            "is_daily_pick": self.is_daily_pick,
            "is_read": self.is_read,
            "is_bookmarked": self.is_bookmarked,
        }


class DailyReport(Base):
    __tablename__ = "daily_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date, unique=True, nullable=False)
    sections = Column(JSON, nullable=False, default=list)
    article_ids = Column(JSON, nullable=False, default=list)
    generated_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self, article_map: dict[int, dict] | None = None):
        result = {
            "id": self.id,
            "date": self.date.isoformat() if self.date else None,
            "sections": self.sections or [],
            "article_ids": self.article_ids or [],
            "generated_at": self.generated_at.isoformat() if self.generated_at else None,
        }
        if article_map:
            for section in result["sections"]:
                section["articles"] = [
                    article_map.get(aid) for aid in section.get("article_ids", [])
                    if article_map.get(aid)
                ]
        return result


class FetchLog(Base):
    __tablename__ = "fetch_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(32), nullable=False)
    source_name = Column(String(256), nullable=False)
    articles_found = Column(Integer, default=0)
    articles_new = Column(Integer, default=0)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "articles_found": self.articles_found,
            "articles_new": self.articles_new,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
        }
