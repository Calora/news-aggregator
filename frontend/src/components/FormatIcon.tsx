import type { Format } from '../types'

const formatConfig: Record<Format, { icon: string; label: string; color: string }> = {
  '学术论文': { icon: '📄', label: '论文', color: 'text-purple-500' },
  '工程实践': { icon: '🛠️', label: '工程', color: 'text-green-500' },
  '政策法规': { icon: '📋', label: '政策', color: 'text-red-500' },
  '行业动态': { icon: '📰', label: '动态', color: 'text-blue-500' },
}

interface Props {
  format: Format
  sourceType?: string
}

export default function FormatIcon({ format, sourceType }: Props) {
  const c = formatConfig[format] ?? { icon: '📌', label: format, color: 'text-gray-400' }

  return (
    <span className={`inline-flex items-center gap-1 font-medium text-xs ${c.color}`}>
      <span>{c.icon}</span>
      <span>{c.label}</span>
      {sourceType === 'CONF' && (
        <span className="px-1 py-0.5 rounded text-[9px] font-bold bg-amber-100 text-amber-700 border border-amber-200">
          CCF-A
        </span>
      )}
    </span>
  )
}
