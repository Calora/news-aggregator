import type { Domain } from '../types'

const domainConfig: Record<Domain, { bg: string; text: string; label: string }> = {
  Blockchain: { bg: 'bg-blue-100', text: 'text-blue-700', label: '区块链' },
  AI: { bg: 'bg-orange-100', text: 'text-orange-700', label: 'AI' },
  'Crypto & Privacy': { bg: 'bg-purple-100', text: 'text-purple-700', label: '密码学与隐私' },
  '数字资产': { bg: 'bg-green-100', text: 'text-green-700', label: '数字资产' },
}

export default function DomainBadge({ domain }: { domain: Domain }) {
  const c = domainConfig[domain] ?? { bg: 'bg-gray-100', text: 'text-gray-600', label: domain }
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${c.bg} ${c.text}`}>
      {c.label}
    </span>
  )
}
