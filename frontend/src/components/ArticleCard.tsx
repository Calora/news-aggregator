import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Article } from '../types'
import { api } from '../api/client'
import DomainBadge from './DomainBadge'

interface Props {
  article: Article
  compact?: boolean
}

export default function ArticleCard({ article, compact }: Props) {
  const queryClient = useQueryClient()

  const bookmarkMutation = useMutation({
    mutationFn: () => api.toggleBookmark(article.id),
    onSuccess: (data) => {
      article.is_bookmarked = data.bookmarked
      queryClient.invalidateQueries({ queryKey: ['articles'] })
      queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
    },
  })

  const timeAgo = getTimeAgo(article.publish_date)

  return (
    <div className="bg-white rounded-xl p-5 shadow-sm hover:shadow-md transition-shadow border border-slate-100">
      {/* Top row: meta + actions */}
      <div className="flex items-center justify-between mb-2.5">
        <div className="flex items-center gap-2 text-xs text-gray-400">
          <span>{_fmtEmoji(article.format)} {article.format}</span>
          <span>·</span>
          <span>{article.source_name}</span>
          <span>·</span>
          <span>{timeAgo}</span>
        </div>
        <div className="flex items-center gap-2">
          <ScoreBadge score={article.relevance_score} />
          <button
            onClick={(e) => { e.preventDefault(); bookmarkMutation.mutate() }}
            className={`shrink-0 text-sm transition-colors ${
              article.is_bookmarked ? 'text-yellow-500' : 'text-gray-300 hover:text-yellow-400'
            }`}
            title={article.is_bookmarked ? '取消收藏' : '收藏'}
          >
            {article.is_bookmarked ? '⭐' : '☆'}
          </button>
        </div>
      </div>

      {/* Domains */}
      {article.domains.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mb-2">
          {article.domains.map((d) => (
            <DomainBadge key={d} domain={d} />
          ))}
        </div>
      )}

      {/* Title */}
      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-base font-bold text-gray-900 hover:text-indigo-600 transition-colors leading-snug block mb-2"
      >
        {article.title}
      </a>

      {/* Summary */}
      <p className="text-sm text-gray-500 leading-relaxed mb-2">
        {article.summary_cn || article.content_preview || '暂无摘要'}
      </p>

      {/* AI Recommendation callout */}
      {article.reason && (
        <div className="bg-amber-50/70 rounded-lg p-3 mt-2 mb-2">
          <p className="text-xs text-amber-800 leading-relaxed">
            <span className="font-medium">💡 推荐理由：</span>{article.reason.replace(/^推荐理由[：:]?\s*/g, '').replace(/^评分\s*\d+\s*分[：:]\s*/g, '')}
          </p>
        </div>
      )}

      {/* Tags - pill style */}
      {article.tags.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2">
          {article.tags.slice(0, 6).map((tag) => (
            <span key={tag} className="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium bg-slate-100 text-slate-600">
              {tag}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 9
      ? 'bg-red-50 text-red-600 border-red-200'
      : score >= 8
        ? 'bg-orange-50 text-orange-600 border-orange-200'
        : 'bg-yellow-50 text-yellow-500 border-yellow-200'
  return (
    <span className={`inline-flex items-center gap-0.5 px-2.5 py-0.5 rounded-full text-xs font-bold border ${color}`}>
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

function getTimeAgo(dateStr: string): string {
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then
  const hours = Math.floor(diff / 3600000)
  if (hours < 1) return '刚刚'
  if (hours < 24) return `${hours}小时前`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}天前`
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
