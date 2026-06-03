export default function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 9
      ? 'bg-red-50 text-red-600 border-red-200'
      : score >= 8
        ? 'bg-orange-50 text-orange-600 border-orange-200'
        : score >= 7
          ? 'bg-yellow-50 text-yellow-600 border-yellow-200'
          : 'bg-gray-50 text-gray-400 border-gray-200'

  return (
    <span
      className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-bold border ${color}`}
    >
      <span className="text-[10px]">★</span>
      {score}
    </span>
  )
}
