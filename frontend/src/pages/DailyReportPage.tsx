import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Article, Domain } from '../types'
import { useEffect, useState } from 'react'

const domainOrder: Domain[] = ['Blockchain', 'AI', '数字资产', 'Crypto & Privacy']
const domainMeta: Record<Domain, { label: string; emoji: string; color: string; border: string }> = {
  Blockchain: { label: '区块链', emoji: '🟦', color: 'text-blue-700', border: 'border-blue-400' },
  AI: { label: 'AI', emoji: '🟧', color: 'text-orange-700', border: 'border-orange-400' },
  'Crypto & Privacy': { label: '密码学与隐私计算', emoji: '🟪', color: 'text-purple-700', border: 'border-purple-400' },
  '数字资产': { label: '数字资产', emoji: '🟢', color: 'text-green-700', border: 'border-green-400' },
}

export default function DailyReportPage() {
  const queryClient = useQueryClient()
  const [selectedDate, setSelectedDate] = useState<string>('')  // '' = today

  // Fetch report list (sidebar)
  const { data: reportList } = useQuery({
    queryKey: ['reportList'],
    queryFn: api.getReportList,
  })

  useEffect(() => {
    if (!selectedDate && reportList?.length) {
      setSelectedDate(reportList[0].date)
    }
  }, [reportList, selectedDate])

  // Fetch current report
  const { data: report, isLoading } = useQuery({
    queryKey: ['dailyReport', selectedDate],
    queryFn: () => (selectedDate ? api.getReport(selectedDate) : api.getTodayReport()),
  })

  const generateMutation = useMutation({
    mutationFn: (date?: string) => api.generateReport(date),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dailyReport'] })
      queryClient.invalidateQueries({ queryKey: ['reportList'] })
    },
  })

  const sections = report?.sections ?? []
  const totalArticles = sections.reduce(
    (sum, s) => sum + ((s as any).articles?.length ?? (s as any).article_ids?.length ?? 0), 0,
  )

  const todayStr = report?.date ? formatDate(report.date) : formatDate(today())
  const isToday = !selectedDate || selectedDate === today()
  const isLatestArchived = selectedDate === reportList?.[0]?.date

  return (
    <div className="flex gap-8">
      {/* ── Sidebar: Date Archive ── */}
      <aside className="w-56 shrink-0 hidden md:block">
        <div className="sticky top-16">
          <h3 className="text-[11px] font-medium text-gray-400 uppercase tracking-wider mb-4">日报归档</h3>

          {/* Date list */}
          <div className="space-y-2 max-h-[calc(100vh-200px)] overflow-y-auto pr-1">
            {(reportList || []).map((item, idx) => {
              const d = new Date(item.date)
              const day = d.getDate()
              const month = d.getMonth() + 1
              const weekdays = ['日', '一', '二', '三', '四', '五', '六']
              const wd = weekdays[d.getDay()]
              const isSelected = selectedDate === item.date || (!selectedDate && idx === 0)
              const isLatest = idx === 0
              return (
                <button
                  key={item.date}
                  onClick={() => setSelectedDate(item.date)}
                  className={`w-full text-left px-3 py-3 rounded-xl transition-colors border ${
                    isSelected
                      ? 'bg-gray-50 border-gray-200'
                      : 'border-transparent hover:bg-gray-50 hover:border-gray-100'
                  }`}
                >
                  <div className="flex items-baseline justify-between mb-1">
                    <span className={`text-sm font-bold ${isSelected ? 'text-gray-900' : 'text-gray-700'}`}>
                      {month} 月 {day} 日
                      {isLatest && <span className='ml-1.5 text-[10px] font-normal text-blue-500 bg-blue-50 px-1.5 py-0.5 rounded-full'>最新</span>}
                    </span>
                    <span className={`text-[10px] ${isSelected ? 'text-gray-400' : 'text-gray-300'}`}>
                      周{wd}
                    </span>
                  </div>
                  {item.headline ? (
                    <p className={`text-xs leading-relaxed line-clamp-2 ${isSelected ? 'text-gray-600' : 'text-gray-400'}`}>
                      {item.headline}
                    </p>
                  ) : item.article_count > 0 ? (
                    <p className='text-xs text-gray-400'>含 {item.article_count} 条精选</p>
                  ) : (
                    <p className='text-xs text-gray-300 italic'>暂无内容</p>
                  )}
                  {item.article_count > 0 && item.headline && (
                    <p className='text-[10px] text-gray-300 mt-1'>{item.article_count} 条精选</p>
                  )}
                </button>
              )
            })}
          </div>
        </div>
      </aside>

      {/* ── Main Content ── */}
      <div className="flex-1 min-w-0">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-xl font-bold text-gray-900 tracking-tight">{todayStr}</h1>
          <p className="text-sm text-gray-400 mt-1">
            {totalArticles > 0
              ? `收录 ${totalArticles} 条精选${!isToday && isLatestArchived ? ' · 最近一期' : ''}`
              : '每 4 小时自动更新 · AI 精选'}
          </p>
        </div>

        {/* Mobile date selector (hidden on desktop) */}
        <div className="md:hidden mb-4 flex gap-2">
          <button
            onClick={() => generateMutation.mutate(undefined)}
            disabled={generateMutation.isPending}
            className="px-4 py-1.5 bg-gray-900 text-white text-xs rounded-lg font-medium"
          >
            生成日报
          </button>
        </div>

        {/* Report content */}
        {isLoading ? (
          <div className="flex justify-center py-20 text-gray-400 text-sm">加载中...</div>
        ) : totalArticles === 0 ? (
          <div className="text-center py-16">
            <p className="text-gray-400 text-sm mb-2">📭 日报尚未生成</p>
            <p className="text-gray-300 text-xs">每 4 小时自动抓取更新，稍后再来</p>
          </div>
        ) : (
          <div className="space-y-8">
            {domainOrder.map((domain) => {
              const section = sections.find((s) => s.domain === domain) as any
              const articles: Article[] = section?.articles || []
              if (articles.length === 0) return null

              const meta = domainMeta[domain]
              return (
                <div key={domain}>
                  <h2 className={`text-sm font-bold mb-3 pb-1.5 border-b-2 ${meta.border} ${meta.color}`}>
                    {meta.emoji} {meta.label}
                    <span className="text-xs text-gray-400 font-normal ml-2">{articles.length} 条</span>
                  </h2>
                  <div className="space-y-4">
                    {articles.map((article: Article) => (
                      <ReportItem key={article.id} article={article} />
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

// ── Report Item ──

function ReportItem({ article }: { article: Article }) {
  const queryClient = useQueryClient()
  const tags = asList(article.tags)

  const bookmarkMutation = useMutation({
    mutationFn: () => api.toggleBookmark(article.id),
    onSuccess: (data) => {
      article.is_bookmarked = data.bookmarked
      queryClient.invalidateQueries({ queryKey: ['dailyReport'] })
    },
  })

  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-slate-100 hover:shadow-md transition-shadow">
      <div className="flex items-start gap-3">
        <div className="shrink-0 mt-0.5">
          <ScoreBadge score={article.relevance_score} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 text-xs text-gray-400 mb-1">
            <span>{_fmtEmoji(article.format)}</span>
            <span>{article.source_name}</span>
            <button
              onClick={(e) => { e.preventDefault(); bookmarkMutation.mutate() }}
              className={`ml-auto text-sm ${article.is_bookmarked ? 'text-yellow-500' : 'text-gray-300 hover:text-yellow-400'}`}
              title={article.is_bookmarked ? '取消收藏' : '收藏'}
            >
              {article.is_bookmarked ? '⭐' : '☆'}
            </button>
          </div>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-base font-bold text-gray-900 hover:text-indigo-600 transition-colors leading-snug"
          >
            {article.title}
          </a>
          {article.summary_cn && (
            <p className="text-sm text-gray-500 mt-1.5 leading-relaxed">{article.summary_cn}</p>
          )}
          {article.reason && (
            <div className="bg-amber-50/70 rounded-lg p-2.5 mt-2">
              <p className="text-xs text-amber-800 leading-relaxed">
                <span className="font-medium">💡 推荐理由：</span>{article.reason.replace(/^推荐理由[：:]?\s*/g, '').replace(/^评分\s*\d+\s*分[：:]\s*/g, '')}
              </p>
            </div>
          )}
          {tags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-2">
              {tags.slice(0, 4).map((tag) => (
                <span key={tag} className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-slate-100 text-slate-600">{tag}</span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 9 ? 'bg-red-50 text-red-600 border-red-200' :
    score >= 8 ? 'bg-orange-50 text-orange-600 border-orange-200' :
    'bg-yellow-50 text-yellow-600 border-yellow-200'
  return (
    <span className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-bold border ${color}`}>
      ★{score}
    </span>
  )
}

function _fmtEmoji(f: string): string {
  switch (f) {
    case '学术论文': return '📄'
    case '工程实践': return '🛠️'
    case '政策法规': return '📋'
    case '行业动态': return '📰'
    default: return '📌'
  }
}

function asList(value: unknown): string[] {
  if (Array.isArray(value)) return value.filter((item): item is string => typeof item === 'string')
  if (typeof value === 'string') {
    if (['Blockchain', 'AI', '数字资产', 'Crypto & Privacy'].includes(value)) return [value]
    const domains: string[] = []
    let remaining = value
    for (const domain of ['Crypto & Privacy', 'Blockchain', 'AI', '数字资产']) {
      if (remaining.includes(domain)) {
        domains.push(domain)
        remaining = remaining.replace(domain, ' ')
      }
    }
    if (domains.length > 0 && remaining.trim().replace(/[ ,;|/]+/g, '') === '') return domains
    return value.split(/[ ,;|/]+/).filter(Boolean)
  }
  return []
}

function today(): string {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日　星期${weekdays[d.getDay()]}`
}
