import type { ScoreCell } from "../api/papers";

export default function ScoreBar({
  label,
  cell,
  emphasis = false,
}: {
  label: string;
  cell: ScoreCell;
  emphasis?: boolean;
}) {
  const pct = cell.value == null ? 0 : Math.round(Math.min(1, Math.max(0, cell.value)) * 100);
  const barColor = emphasis ? "bg-accent" : "bg-ink/40";

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between">
        <span className="text-xs text-muted">{label}</span>
        <span className={`text-sm tabular-nums ${emphasis ? "font-semibold text-ink" : "text-ink"}`}>
          {cell.status === "ready" && cell.value != null
            ? cell.value.toFixed(2)
            : cell.status === "pending"
              ? "scoring…"
              : "unavailable"}
        </span>
      </div>
      <div className="h-1 overflow-hidden rounded-full bg-hairline">
        {cell.status === "ready" && cell.value != null && (
          <div className={`h-full rounded-full ${barColor} transition-[width]`} style={{ width: `${pct}%` }} />
        )}
      </div>
    </div>
  );
}
