import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import ArticleCard from '../components/ArticleCard'

export default function BookmarksPage() {
  const [page, setPage] = useState(1)

  const { data, isLoading } = useQuery({
    queryKey: ['bookmarks', page],
    queryFn: () => api.getBookmarks(page, 20),
  })

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 mb-1">⭐ 我的收藏</h1>
      <p className="text-sm text-gray-400 mb-6">标记为稍后精读的文章</p>

      {isLoading ? (
        <div className="text-center py-16 text-gray-400 text-sm">加载中...</div>
      ) : !data || data.total === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 text-sm mb-2">📭 还没有收藏任何文章</p>
          <p className="text-gray-300 text-xs">在「全部动态」中点击 ☆ 即可收藏感兴趣的文章</p>
        </div>
      ) : (
        <>
          <div className="text-xs text-gray-400 mb-3">
            共 {data.total} 篇
          </div>
          <div className="space-y-4">
            {data.items.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
          {data.total > 20 && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-30"
              >
                上一页
              </button>
              <span className="px-3 py-1.5 text-xs text-gray-500">
                {page} / {Math.ceil(data.total / 20)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(data.total / 20)}
                className="px-3 py-1.5 text-xs border rounded-lg disabled:opacity-30"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
