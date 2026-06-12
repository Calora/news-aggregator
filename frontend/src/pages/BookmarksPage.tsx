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

  const syncMutation = useMutation({
    mutationFn: () => api.syncToFeishu([]),
    onSuccess: (res) => {
      if (res.ok) {
        setResult(res)
        queryClient.invalidateQueries({ queryKey: ['bookmarks'] })
      } else {
        setResult({ error: res.error || '同步失败' })
      }
    },
    onError: () => setResult({ error: '同步请求失败，请检查后端' }),
  })

  const [result, setResult] = useState<any>(null)

  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <h1 className="text-xl font-bold text-gray-900">⭐ 我的收藏</h1>
        {data && data.total > 0 && (
          <button
            onClick={() => { setResult(null); syncMutation.mutate() }}
            disabled={syncMutation.isPending}
            className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {syncMutation.isPending ? '⟳ 同步中...' : '📤 同步到飞书'}
          </button>
        )}
      </div>
      <p className="text-sm text-gray-400 mb-6">标记为稍后精读的文章</p>

      {/* Sync result */}
      {result && !result.error && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 mb-6">
          <p className="text-sm font-medium text-emerald-800 mb-2">✓ 同步完成</p>
          <div className="text-xs text-emerald-700 space-y-1">
            <p>收藏总数：{result.total_bookmarks} 篇</p>
            <p>本次新增同步：{result.new_synced} 篇</p>
            {result.already_synced > 0 && <p>此前已同步：{result.already_synced} 篇</p>}
            {result.material_doc && (
              <a href={result.material_doc} target="_blank" rel="noreferrer" className="block text-emerald-700 hover:underline">
                📄 素材汇总文档 → 打开
              </a>
            )}
            <a href={result.topic_doc} target="_blank" rel="noreferrer" className="block text-emerald-700 hover:underline">
              💡 选题推荐文档 → 打开
            </a>
          </div>
        </div>
      )}

      {result?.error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <p className="text-sm text-red-700">{result.error}</p>
        </div>
      )}

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
