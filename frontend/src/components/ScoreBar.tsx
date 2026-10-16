import type { ScoreCell } from "../api/papers";

// Placeholder descriptions shown on hover/focus of a score's info marker.
// TODO: replace with the real, agreed copy once product defines it.
const HINTS: Record<string, string> = {
  Relevance: "Placeholder: how well this paper matches your search. (Final copy pending.)",
  Reproducibility:
    "Placeholder: how reproducible the paper's results appear, from its code and setup. (Final copy pending.)",
  Overall:
    "Placeholder: a combined ranking of relevance and reproducibility. (Final copy pending.)",
  "Code quality": "Placeholder: an assessment of the generated code's quality. (Final copy pending.)",
  "Setup completeness":
    "Placeholder: how complete the paper's experiment setup is. (Final copy pending.)",
};

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
  const hint = HINTS[label];

  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between">
        <span className="flex items-center gap-1 text-xs text-muted">
          {label}
          {hint && (
            <span
              tabIndex={0}
              role="img"
              aria-label={`${label}: ${hint}`}
              title={hint}
              className="cursor-help rounded-full text-[10px] text-muted focus-visible:ring-2 focus-visible:ring-accent/40"
            >
              ⓘ
            </span>
          )}
        </span>
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
