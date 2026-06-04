import type { Article, ArticleFilter, ArticleListResponse, DailyReport, EmailAccount, FetchLog, WebSource } from '../types'

const BASE = '/api'

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const err = await res.text()
    throw new Error(err || `${res.status} ${res.statusText}`)
  }
  return res.json()
}

export const api = {
  // Articles
  getArticles: (filter: ArticleFilter) =>
    request<ArticleListResponse>('/articles?' + new URLSearchParams(toQuery(filter))),

  getArticle: (id: number) =>
    request<Article>(`/articles/${id}`),

  toggleBookmark: (id: number) =>
    request<{ ok: boolean; bookmarked: boolean }>(`/articles/${id}/bookmark`, { method: 'POST' }),

  getBookmarks: (page = 1, pageSize = 20) =>
    request<ArticleListResponse>(`/bookmarks?page=${page}&page_size=${pageSize}`),

  // Daily Report
  getTodayReport: () =>
    request<DailyReport>('/report/today'),

  getReport: (date: string) =>
    request<DailyReport>(`/report/${date}`),

  getReportList: () =>
    request<{ date: string; headline: string; article_count: number }[]>('/report/list'),

  generateReport: (targetDate?: string) =>
    request<DailyReport>(`/report/generate${targetDate ? `?target_date=${targetDate}` : ''}`, { method: 'POST' }),

  // Sources - Email
  getEmailAccounts: () =>
    request<EmailAccount[]>('/sources/email'),

  createEmailAccount: (data: Partial<EmailAccount>) =>
    request<EmailAccount>('/sources/email', { method: 'POST', body: JSON.stringify(data) }),

  updateEmailAccount: (id: number, data: Partial<EmailAccount>) =>
    request<EmailAccount>(`/sources/email/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteEmailAccount: (id: number) =>
    request<void>(`/sources/email/${id}`, { method: 'DELETE' }),

  testEmailAccount: (id: number) =>
    request<{ ok: boolean; message: string }>(`/sources/email/${id}/test`, { method: 'POST' }),

  // Sources - Web
  getWebSources: () =>
    request<WebSource[]>('/sources/web'),

  createWebSource: (data: Partial<WebSource>) =>
    request<WebSource>('/sources/web', { method: 'POST', body: JSON.stringify(data) }),

  updateWebSource: (id: number, data: Partial<WebSource>) =>
    request<WebSource>(`/sources/web/${id}`, { method: 'PUT', body: JSON.stringify(data) }),

  deleteWebSource: (id: number) =>
    request<void>(`/sources/web/${id}`, { method: 'DELETE' }),

  testWebSource: (url: string) =>
    request<{ ok: boolean; message: string }>('/sources/web/test', { method: 'POST', body: JSON.stringify({ url }) }),

  // Fetch
  triggerFetch: () =>
    request<{ ok: boolean; message: string }>('/fetch', { method: 'POST' }),

  reprocessAll: () =>
    request<{ ok: boolean; message: string }>('/reprocess', { method: 'POST' }),

  dedupArticles: () =>
    request<{ ok: boolean; message: string }>('/dedup', { method: 'POST' }),

  getFetchLogs: (limit?: number) =>
    request<FetchLog[]>(`/fetch/logs?limit=${limit ?? 20}`),
}

function toQuery(filter: ArticleFilter): Record<string, string> {
  const q: Record<string, string> = {}
  if (filter.domains?.length) q.domains = filter.domains.join(',')
  if (filter.formats?.length) q.formats = filter.formats.join(',')
  if (filter.tags?.length) q.tags = filter.tags.join(',')
  if (filter.score_min !== undefined) q.score_min = String(filter.score_min)
  if (filter.score_max !== undefined) q.score_max = String(filter.score_max)
  if (filter.date_from) q.date_from = filter.date_from
  if (filter.date_to) q.date_to = filter.date_to
  if (filter.keyword) q.keyword = filter.keyword
  if (filter.page !== undefined) q.page = String(filter.page)
  if (filter.page_size !== undefined) q.page_size = String(filter.page_size)
  return q
}
