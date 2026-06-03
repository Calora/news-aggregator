export type Domain = 'Blockchain' | 'AI' | 'Crypto & Privacy' | '数字资产'

export type Format = '学术论文' | '工程实践' | '政策法规' | '行业动态'

export interface Article {
  id: number
  title: string
  url: string
  source_type: string
  source_name: string
  content_preview: string | null
  authors: string | null
  publish_date: string
  fetched_at: string
  domains: Domain[]
  tags: string[]
  format: Format
  relevance_score: number
  summary_cn: string | null
  reason: string | null
  is_daily_pick: boolean
  is_read: boolean
  is_bookmarked: boolean
}

export interface DailyReport {
  id: number
  date: string
  sections: ReportSection[]
  article_ids: number[]
  generated_at: string
}

export interface ReportSection {
  domain: Domain
  label?: string
  articles?: Article[]
  article_ids?: number[]
}

export interface EmailAccount {
  id: number
  email: string
  imap_server: string
  imap_port: number
  enabled: boolean
  last_fetch_at: string | null
}

export interface WebSource {
  id: number
  name: string
  url: string
  source_type: string
  enabled: boolean
}

export interface FetchLog {
  id: number
  source_type: string
  source_name: string
  articles_found: number
  articles_new: number
  fetched_at: string
}

export interface ArticleListResponse {
  items: Article[]
  total: number
  page: number
  page_size: number
}

export interface ArticleFilter {
  domains?: Domain[]
  formats?: Format[]
  tags?: string[]
  score_min?: number
  score_max?: number
  date_from?: string
  date_to?: string
  keyword?: string
  page?: number
  page_size?: number
}
