export default function TagBadge({ tag }: { tag: string }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-md text-[11px] bg-gray-50 text-gray-500 border border-gray-100">
      {tag}
    </span>
  )
}
