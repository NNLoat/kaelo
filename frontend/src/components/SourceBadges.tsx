export default function SourceBadges({ sources }: { sources: string[] }) {
  if (sources.length === 0) return null;
  return (
    <div className="flex flex-wrap gap-1.5">
      {sources.map((s) => (
        <span
          key={s}
          className="rounded border border-hairline bg-white px-1.5 py-0.5 text-xs capitalize text-muted"
        >
          {s}
        </span>
      ))}
    </div>
  );
}
