import type { SortKey } from "./useScorePolling";

const OPTIONS: { key: SortKey; label: string }[] = [
  { key: "relevance", label: "Relevance" },
  { key: "final", label: "Final score" },
];

// Segmented toggle for the result sort key. Relevance is the default (it lands
// first); Final score (relevance + reproducibility) is opt-in and re-sorts on
// click. Switching is an explicit event — the list only reorders here, never
// while reproducibility scores stream in under the reader.
export default function SortControl({
  value,
  onChange,
}: {
  value: SortKey;
  onChange: (key: SortKey) => void;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-muted">Sort by</span>
      <div
        role="radiogroup"
        aria-label="Sort results by"
        className="inline-flex rounded-md border border-hairline bg-white p-0.5"
      >
        {OPTIONS.map((opt) => {
          const active = value === opt.key;
          return (
            <button
              key={opt.key}
              role="radio"
              aria-checked={active}
              onClick={() => onChange(opt.key)}
              className={`rounded px-3 py-1 text-sm transition focus-visible:ring-2 focus-visible:ring-accent/40 ${
                active ? "bg-accent text-white" : "text-ink hover:bg-paper"
              }`}
            >
              {opt.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
