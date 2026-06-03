import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../api/client'
import type { EmailAccount, WebSource } from '../types'

export default function SourcesPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<'email' | 'web' | 'logs'>('email')
  const [fetchResult, setFetchResult] = useState<{ msg: string; ok: boolean } | null>(null)

  useEffect(() => {
    if (fetchResult) {
      const t = setTimeout(() => setFetchResult(null), 6000)
      return () => clearTimeout(t)
    }
  }, [fetchResult])

  const fetchMutation = useMutation({
    mutationFn: api.triggerFetch,
    onSuccess: (res) => {
      setFetchResult({ msg: res.message, ok: true })
      queryClient.invalidateQueries({ queryKey: ['fetchLogs'] })
    },
    onError: () => setFetchResult({ msg: '抓取失败，请检查后端是否运行', ok: false }),
  })

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-900">数据源管理</h1>
        <div className="flex flex-col items-end gap-1">
          <button
            onClick={() => fetchMutation.mutate()}
            disabled={fetchMutation.isPending}
            className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {fetchMutation.isPending ? '⟳ 正在抓取...' : '手动抓取'}
          </button>
          {fetchResult && (
            <span
              onClick={() => setFetchResult(null)}
              className={`text-xs px-2 py-1 rounded cursor-pointer ${
                fetchResult.ok ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
              }`}
            >
              {fetchResult.ok ? '✓ ' : '✗ '}{fetchResult.msg}
            </span>
          )}
        </div>
      </div>

      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {(['email', 'web', 'logs'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm border-b-2 transition-colors ${
              activeTab === tab
                ? 'border-blue-600 text-blue-600 font-medium'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {{ email: '邮箱账号', web: 'Web 信源', logs: '抓取日志' }[tab]}
          </button>
        ))}
      </div>

      {activeTab === 'email' && <EmailTab />}
      {activeTab === 'web' && <WebTab />}
      {activeTab === 'logs' && <LogsTab />}
    </div>
  )
}

function EmailTab() {
  const queryClient = useQueryClient()
  const { data: accounts, isLoading } = useQuery({
    queryKey: ['emailAccounts'],
    queryFn: api.getEmailAccounts,
  })

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ email: '', auth_code: '', imap_server: 'imap.qq.com', imap_port: 993 })

  const createMutation = useMutation({
    mutationFn: () => api.createEmailAccount(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['emailAccounts'] })
      setShowForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: api.deleteEmailAccount,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['emailAccounts'] }),
  })

  const testMutation = useMutation({
    mutationFn: api.testEmailAccount,
  })

  return (
    <div>
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 mb-4 text-sm text-yellow-800">
        <p className="font-medium mb-1">QQ 邮箱 / 163 邮箱配置提示：</p>
        <ul className="list-disc list-inside space-y-0.5 text-xs">
          <li>QQ邮箱：设置 → 账户 → POP3/IMAP/SMTP → 开启 IMAP → 生成授权码</li>
          <li>163邮箱：设置 → POP3/SMTP/IMAP → 开启 IMAP → 新增授权码</li>
          <li>请填写<b>授权码</b>而非登录密码，系统会加密存储</li>
        </ul>
      </div>

      {!showForm && (
        <button
          onClick={() => setShowForm(true)}
          className="px-3 py-1.5 text-sm border border-dashed rounded-lg text-gray-500 hover:border-blue-300 hover:text-blue-600 transition-colors mb-4"
        >
          + 添加邮箱
        </button>
      )}

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 space-y-3">
          <input
            placeholder="邮箱地址 (如 user@qq.com)"
            value={form.email}
            onChange={(e) => setForm({ ...form, email: e.target.value })}
            className="w-full px-3 py-1.5 text-sm border rounded-lg"
          />
          <input
            placeholder="授权码（非密码）"
            type="password"
            value={form.auth_code}
            onChange={(e) => setForm({ ...form, auth_code: e.target.value })}
            className="w-full px-3 py-1.5 text-sm border rounded-lg"
          />
          <div className="flex gap-2">
            <select
              value={form.imap_server}
              onChange={(e) => {
                const server = e.target.value
                setForm({
                  ...form,
                  imap_server: server,
                  imap_port: server === 'imap.qq.com' ? 993 : server === 'imap.163.com' ? 993 : 993,
                })
              }}
              className="flex-1 px-3 py-1.5 text-sm border rounded-lg"
            >
              <option value="imap.qq.com">QQ邮箱 (imap.qq.com:993)</option>
              <option value="imap.163.com">163邮箱 (imap.163.com:993)</option>
              <option value="imap.gmail.com">Gmail (imap.gmail.com:993)</option>
              <option value="">自定义</option>
            </select>
            <input
              type="number"
              placeholder="端口"
              value={form.imap_port}
              onChange={(e) => setForm({ ...form, imap_port: Number(e.target.value) })}
              className="w-24 px-3 py-1.5 text-sm border rounded-lg"
            />
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending}
              className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              保存
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-1.5 text-sm border rounded-lg text-gray-500 hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-gray-400 text-sm">加载中...</div>
      ) : (
        <div className="space-y-2">
          {(accounts ?? []).map((acc) => (
            <div key={acc.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-3">
              <div>
                <span className="text-sm font-medium text-gray-900">{acc.email}</span>
                <span className="text-xs text-gray-400 ml-2">{acc.imap_server}:{acc.imap_port}</span>
                {acc.last_fetch_at && (
                  <span className="text-xs text-gray-400 ml-2">
                    上次抓取: {new Date(acc.last_fetch_at).toLocaleString('zh-CN')}
                  </span>
                )}
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => testMutation.mutate(acc.id)}
                  className="px-2 py-1 text-xs border rounded text-gray-500 hover:bg-gray-50"
                >
                  测试
                </button>
                <button
                  onClick={() => deleteMutation.mutate(acc.id)}
                  className="px-2 py-1 text-xs border rounded text-red-500 hover:bg-red-50"
                >
                  删除
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function WebTab() {
  const queryClient = useQueryClient()
  const { data: sources, isLoading } = useQuery({
    queryKey: ['webSources'],
    queryFn: api.getWebSources,
  })

  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', url: '', source_type: 'RSS' })

  const createMutation = useMutation({
    mutationFn: () => api.createWebSource(form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['webSources'] })
      setShowForm(false)
    },
  })

  const deleteMutation = useMutation({
    mutationFn: api.deleteWebSource,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['webSources'] }),
  })

  const builtInSources = [
    { name: 'InfoQ', url: 'https://feed.infoq.com/', type: 'RSS', group: '用户订阅' },
    { name: 'Medium (Blockchain)', url: 'https://medium.com/feed/tag/blockchain', type: 'RSS', group: '用户订阅' },
    { name: 'Ethresear.ch', url: 'https://ethresear.ch/posts.rss', type: 'RSS', group: '区块链' },
    { name: 'The Block', url: 'https://www.theblock.co/rss', type: 'RSS', group: '区块链' },
    { name: 'Messari', url: 'https://messari.io/feed', type: 'RSS', group: '区块链' },
    { name: 'a16z Crypto', url: 'https://a16zcrypto.com/feed/', type: 'RSS', group: '区块链' },
    { name: 'CoinTelegraph', url: 'https://cointelegraph.com/rss', type: 'RSS', group: '区块链' },
    { name: 'Decrypt', url: 'https://decrypt.co/feed', type: 'RSS', group: '区块链' },
    { name: 'IACR ePrint', url: 'https://eprint.iacr.org/rss', type: 'RSS', group: 'ZK/密码学' },
    { name: 'ZK Mesh', url: 'https://zkmesh.substack.com/feed', type: 'RSS', group: 'ZK/密码学' },
    { name: 'Zero Knowledge Blog', url: 'https://zeroknowledge.fm/feed', type: 'RSS', group: 'ZK/密码学' },
    { name: 'Hacker News', url: 'https://hnrss.org/frontpage', type: 'RSS', group: 'AI/技术' },
  ]

  return (
    <div>
      <div className="mb-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">预置信源（点击快速添加）</h3>
{(['用户订阅', '区块链', 'ZK/密码学', 'AI/技术'] as const).map((group) => {
          const sources = builtInSources.filter((s) => (s as any).group === group)
          if (sources.length === 0) return null
          return (
            <div key={group} className="mb-2">
              <span className="text-[10px] text-gray-400 font-medium mr-2">{group}</span>
              <div className="flex flex-wrap gap-1.5 mt-1">
                {sources.map((s) => (
                  <button
                    key={s.url}
                    onClick={() => {
                      setForm({ name: s.name, url: s.url, source_type: s.type })
                      setShowForm(true)
                    }}
                    className="px-2 py-1 text-xs border rounded-lg text-gray-500 hover:border-blue-300 hover:text-blue-600 transition-colors"
                  >
                    + {s.name}
                  </button>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      {showForm && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-4 space-y-3">
          <input
            placeholder="信源名称"
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            className="w-full px-3 py-1.5 text-sm border rounded-lg"
          />
          <input
            placeholder="URL (RSS/网页)"
            value={form.url}
            onChange={(e) => setForm({ ...form, url: e.target.value })}
            className="w-full px-3 py-1.5 text-sm border rounded-lg"
          />
          <select
            value={form.source_type}
            onChange={(e) => setForm({ ...form, source_type: e.target.value })}
            className="w-full px-3 py-1.5 text-sm border rounded-lg"
          >
            <option value="RSS">RSS</option>
            <option value="WEB">网页抓取</option>
            <option value="ARXIV">arXiv API</option>
          </select>
          <div className="flex gap-2">
            <button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending}
              className="px-4 py-1.5 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              保存
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="px-4 py-1.5 text-sm border rounded-lg text-gray-500 hover:bg-gray-50"
            >
              取消
            </button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="text-gray-400 text-sm">加载中...</div>
      ) : (
        <div className="space-y-2">
          {(sources ?? []).map((src) => (
            <div key={src.id} className="flex items-center justify-between bg-white border border-gray-200 rounded-lg p-3">
              <div>
                <span className="text-sm font-medium text-gray-900">{src.name}</span>
                <span className="text-xs text-gray-400 ml-2">{src.source_type}</span>
                <span className="text-xs text-gray-400 ml-2 truncate max-w-xs">{src.url}</span>
              </div>
              <button
                onClick={() => deleteMutation.mutate(src.id)}
                className="px-2 py-1 text-xs border rounded text-red-500 hover:bg-red-50"
              >
                删除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function LogsTab() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ['fetchLogs'],
    queryFn: () => api.getFetchLogs(30),
  })

  if (isLoading) return <div className="text-gray-400 text-sm">加载中...</div>

  return (
    <div className="space-y-1">
      {(logs ?? []).map((log) => (
        <div key={log.id} className="flex items-center justify-between text-sm py-2 border-b border-gray-100">
          <div>
            <span className="text-gray-700">{log.source_name}</span>
            <span className="text-xs text-gray-400 ml-2">({log.source_type})</span>
          </div>
          <div className="text-xs text-gray-400">
            找到 {log.articles_found} 条 · 新增 {log.articles_new} 条 · {new Date(log.fetched_at).toLocaleString('zh-CN')}
          </div>
        </div>
      ))}
    </div>
  )
}
