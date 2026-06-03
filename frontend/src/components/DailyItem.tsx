import type { Article } from '../types'
import ScoreBadge from './ScoreBadge'
import TagBadge from './TagBadge'

interface Props {
  article: Article
}

export default function DailyItem({ article }: Props) {
  return (
    <div className="py-2.5 border-b border-gray-50 last:border-0">
      <div className="flex items-start gap-3">
        <div className="flex-1 min-w-0">
          {/* Title row: format icon + title + score */}
          <div className="flex items-start gap-2">
            <span className="text-xs shrink-0 mt-0.5">
              {_formatEmoji(article.format)}
              {article.source_type === 'CONF' && (
                <span className="ml-1 px-1 py-0.5 rounded text-[9px] font-bold bg-amber-100 text-amber-700 border border-amber-200">
                  CCF-A
                </span>
              )}
            </span>
            <a
              href={article.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-semibold text-gray-900 hover:text-blue-600 transition-colors leading-snug flex-1"
            >
              {article.title}
            </a>
            <ScoreBadge score={article.relevance_score} />
          </div>

          {/* Summary */}
          {article.summary_cn && (
            <p className="text-xs text-gray-500 mt-1 ml-5 leading-relaxed">
              {article.summary_cn}
            </p>
          )}

          {/* Reason */}
          {article.reason && (
            <p className="text-xs text-blue-600 mt-1 ml-5">
              💡 {article.reason}
            </p>
          )}

          {/* Footer: source + tags */}
          <div className="flex items-center gap-2 mt-1.5 ml-5 text-[11px] text-gray-400">
            <span>{article.source_name}</span>
            {article.tags.length > 0 && (
              <>
                <span>·</span>
                <div className="flex flex-wrap gap-1">
                  {article.tags.slice(0, 4).map((tag) => (
                    <TagBadge key={tag} tag={tag} />
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

function _formatEmoji(format: string): string {
  switch (format) {
    case '学术论文': return '📄'
    case '工程实践': return '🛠️'
    case '政策法规': return '📋'
    case '行业动态': return '📰'
    default: return '📌'
  }
}
