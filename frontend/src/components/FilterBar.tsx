import type { Domain, Format } from '../types'

const domains: Domain[] = ['Blockchain', 'AI', '数字资产', 'Crypto & Privacy']
const formats: Format[] = ['工程实践', '行业动态', '政策法规']

interface Props {
  selectedDomains: Domain[]
  selectedFormats: Format[]
  keyword: string
  onDomainsChange: (d: Domain[]) => void
  onFormatsChange: (f: Format[]) => void
  onKeywordChange: (k: string) => void
}

export default function FilterBar({
  selectedDomains,
  selectedFormats,
  keyword,
  onDomainsChange,
  onFormatsChange,
  onKeywordChange,
}: Props) {
  const toggleDomain = (d: Domain) => {
    onDomainsChange(
      selectedDomains.includes(d)
        ? selectedDomains.filter((x) => x !== d)
        : [...selectedDomains, d]
    )
  }

  const toggleFormat = (f: Format) => {
    // Single-select: if already selected, deselect (show all); otherwise select only this one
    if (selectedFormats.includes(f)) {
      onFormatsChange([])
    } else {
      onFormatsChange([f])
    }
  }

  return (
    <div className="flex flex-col gap-3 mb-4">
      <input
        type="text"
        value={keyword}
        onChange={(e) => onKeywordChange(e.target.value)}
        placeholder="搜索标题、标签..."
        className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-100 focus:border-blue-300"
      />
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-gray-400 self-center mr-1">领域:</span>
        {domains.map((d) => (
          <button
            key={d}
            onClick={() => toggleDomain(d)}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              selectedDomains.includes(d)
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
          >
            {d}
          </button>
        ))}
      </div>
      <div className="flex flex-wrap gap-2">
        <span className="text-xs text-gray-400 self-center mr-1">类型:</span>
        {formats.map((f) => (
          <button
            key={f}
            onClick={() => toggleFormat(f)}
            className={`px-2 py-1 rounded text-xs font-medium transition-colors ${
              selectedFormats.includes(f)
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
            }`}
          >
            {f}
          </button>
        ))}
      </div>
    </div>
  )
}
