import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../api/client'
import type { Domain, Format } from '../types'
import ArticleCard from '../components/ArticleCard'
import FilterBar from '../components/FilterBar'

export default function AllNewsPage() {
  const [page, setPage] = useState(1)
  const [domains, setDomains] = useState<Domain[]>([])
  const [formats, setFormats] = useState<Format[]>([])
  const [keyword, setKeyword] = useState('')

  const { data, isLoading } = useQuery({
    queryKey: ['articles', { domains, formats, keyword, page }],
    queryFn: () =>
      api.getArticles({
        domains: domains.length ? domains : undefined,
        formats: formats.length ? formats : undefined,
        keyword: keyword || undefined,
        page,
        page_size: 20,
      }),
  })

  return (
    <div>
      <h1 className="text-xl font-bold text-gray-900 mb-4">全部动态</h1>

      <FilterBar
        selectedDomains={domains}
        selectedFormats={formats}
        keyword={keyword}
        onDomainsChange={(d) => { setDomains(d); setPage(1) }}
        onFormatsChange={(f) => { setFormats(f); setPage(1) }}
        onKeywordChange={(k) => { setKeyword(k); setPage(1) }}
      />

      {isLoading ? (
        <div className="text-center py-12 text-gray-400">加载中...</div>
      ) : data && data.total === 0 ? (
        <div className="text-center py-16">
          <p className="text-gray-400 text-sm mb-3">没有匹配的内容</p>
          <p className="text-gray-300 text-xs">
            请先在「数据源」页面点击「AI 重新分析」处理文章
          </p>
        </div>
      ) : (
        <>
          <div className="text-xs text-gray-400 mb-3">
            {data ? `共 ${data.total} 条，第 ${data.page}/${Math.max(1, Math.ceil(data.total / data.page_size))} 页` : ''}
          </div>
          <div className="space-y-4">
            {data?.items.map((article) => (
              <ArticleCard key={article.id} article={article} />
            ))}
          </div>
          {data && data.total > data.page_size && (
            <div className="flex justify-center gap-2 mt-6">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-30"
              >
                上一页
              </button>
              <span className="px-3 py-1.5 text-sm text-gray-500">
                {page} / {Math.ceil(data.total / data.page_size)}
              </span>
              <button
                onClick={() => setPage((p) => p + 1)}
                disabled={page >= Math.ceil(data.total / data.page_size)}
                className="px-3 py-1.5 text-sm border rounded-lg disabled:opacity-30"
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
