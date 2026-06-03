from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


VALID_DOMAINS = {"Blockchain", "AI", "Crypto & Privacy", "数字资产"}
VALID_FORMATS = {"学术论文", "工程实践", "政策法规", "行业动态"}


class EmailAccountCreate(BaseModel):
    email: str
    auth_code: str
    imap_server: str = "imap.qq.com"
    imap_port: int = 993


class EmailAccountUpdate(BaseModel):
    email: Optional[str] = None
    auth_code: Optional[str] = None
    imap_server: Optional[str] = None
    imap_port: Optional[int] = None
    enabled: Optional[bool] = None


class WebSourceCreate(BaseModel):
    name: str
    url: str
    source_type: str = "RSS"


class WebSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    source_type: Optional[str] = None
    enabled: Optional[bool] = None


class ArticleFilter(BaseModel):
    domains: Optional[str] = None      # comma-separated
    formats: Optional[str] = None      # comma-separated
    tags: Optional[str] = None         # comma-separated
    score_min: Optional[int] = None
    score_max: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20


class ArticleResponse(BaseModel):
    items: list[dict]
    total: int
    page: int
    page_size: int
