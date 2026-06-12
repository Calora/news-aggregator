import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import ArticleCard from '../components/ArticleCard'

export default function BookmarksPage() {
  const [page, setPage] = useState(1)
  const queryClient = useQueryClient()

  const { data, isLoading } = useQuery({
    queryKey: ['bookmarks', page],
    queryFn: () => api.getBookmarks(page, 20),
  })

  // Grouping state
  const [grouping, setGrouping] = useState<any>(null)
  const [selectedGroups, setSelectedGroups] = useState<Set<number>>(new Set())
  const [syncedDocs, setSyncedDocs] = useState<any[]>([])
  const [syncError, setSyncError] = useState('')

  const groupMutation = useMutation({
    mutationFn: api.groupBookmarks,
    onSuccess: (res) => {
      setGrouping(res)
      setSyncedDocs([])
      setSyncError('')
      // Auto-select all groups
      if (res.groups) setSelectedGroups(new Set(res.groups.map((_: any, i: number) => i)))
    },
    onError: () => setSyncError('AI 分组失败，请重试'),
  })

  const syncMutation = useMutation({
    mutationFn: api.syncToFeishu,
    onSuccess: (res) => {
      if (res.ok) {
        setSyncedDocs(res.docs_created || [])
        setSyncError(res.errors?.length ? res.errors.map((e: any) => e.error).join('; ') : '')
      } else {
        setSyncError(res.error || '同步失败')
      }
    },
    onError: () => setSyncError('同步请求失败'),
  })

  const toggleGroup = (idx: number) => {
    const next = new Set(selectedGroups)
    if (next.has(idx)) next.delete(idx)
    else next.add(idx)
    setSelectedGroups(next)
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-bold text-gray-900">⭐ 我的收藏</h1>
        {data && data.total > 0 && (
          <button
            onClick={() => groupMutation.mutate()}
            disabled={groupMutation.isPending}
            className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {groupMutation.isPending ? 'AI 分组中...' : grouping ? '🔄 重新分组' : '📤 同步到飞书'}
          </button>
        )}
      </div>
      <p className="text-sm text-gray-400 mb-6">标记为稍后精读的文章</p>

      {/* Grouping result */}
      {grouping && !grouping.error && (
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6">
          <h3 className="text-sm font-bold text-gray-900 mb-3">
            AI 分组结果（共 {grouping.total_bookmarks} 篇收藏，分为 {grouping.groups?.length || 0} 组）
          </h3>

          {grouping.groups?.map((g: any, idx: number) => (
            <div key={idx} className="mb-3 last:mb-0 border border-gray-100 rounded-lg p-3">
              <label className="flex items-start gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedGroups.has(idx)}
                  onChange={() => toggleGroup(idx)}
                  className="mt-0.5"
                />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">📝 {g.topic}</p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {g.articles?.map((a: any) => a.title?.slice(0, 30)).join(' · ')}
                  </p>
                  {g.suggested_titles?.length > 0 && (
                    <div className="mt-2 space-y-0.5">
                      {g.suggested_titles.map((t: string, ti: number) => (
                        <p key={ti} className="text-xs text-blue-600">📌 {t}</p>
                      ))}
                    </div>
                  )}
                </div>
              </label>
            </div>
          ))}

          {grouping.ungrouped_articles?.length > 0 && (
            <p className="text-xs text-gray-400 mt-3">
              📭 {grouping.ungrouped_articles.length} 篇未能分组
            </p>
          )}

          {/* Sync button */}
          <div className="mt-4 flex gap-2 items-center">
            <button
              onClick={() => syncMutation.mutate([...selectedGroups])}
              disabled={syncMutation.isPending || selectedGroups.size === 0}
              className="px-4 py-1.5 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {syncMutation.isPending ? '正在创建文档...' : `同步选中 (${selectedGroups.size}) 到飞书`}
            </button>
            <button
              onClick={() => { setGrouping(null); setSyncedDocs([]); setSyncError('') }}
              className="px-3 py-1.5 text-xs text-gray-500 hover:text-gray-700"
            >
              取消
            </button>
          </div>

          {syncError && (
            <p className="text-xs text-red-500 mt-2">{syncError}</p>
          )}

          {/* Created docs */}
          {syncedDocs.length > 0 && (
            <div className="mt-4 bg-emerald-50 rounded-lg p-3">
              <p className="text-xs font-medium text-emerald-800 mb-2">✓ 已创建 {syncedDocs.length} 个飞书文档：</p>
              {syncedDocs.map((d: any, i: number) => (
                <a key={i} href={d.url} target="_blank" rel="noreferrer"
                   className="block text-xs text-emerald-700 hover:underline mb-1">
                  📄 {d.topic}（{d.article_count} 篇素材）→ 打开文档
                </a>
              ))}
            </div>
          )}
        </div>
      )}

      {grouping?.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-700">分组失败：{grouping.error}</p>
        </div>
      )}

      {/* Article list */}
      {isLoading ? (
        <div className="text-center py-16 text-gray-400 text-sm">加载中...</div>
      ) : !data || data.total === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 text-sm mb-2">📭 还没有收藏任何文章</p>
          <p className="text-gray-300 text-xs">在「全部动态」中点击 ☆ 即可收藏感兴趣的文章</p>
        </div>
      ) : (
        <>
          <div className="text-xs text-gray-400 mb-3">共 {data.total} 篇</div>
          <div className="space-y-4">
            {data.items.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
          {data.total > 20 && (
            <div className="flex justify-center gap-2 mt-6">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}
                      className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-30">上一页</button>
              <span className="px-3 py-1.5 text-xs text-gray-500">{page} / {Math.ceil(data.total / 20)}</span>
              <button onClick={() => setPage((p) => p + 1)} disabled={page >= Math.ceil(data.total / 20)}
                      className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-30">下一页</button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
