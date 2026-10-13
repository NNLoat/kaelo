import { useEffect, useState } from "react";
import { listClaims, isNetworkError, type ClaimRead } from "../../api/writer";

export default function ClaimsList({
  refreshKey,
  onOpen,
}: {
  refreshKey: number;
  onOpen: (claim: ClaimRead) => void;
}) {
  const [claims, setClaims] = useState<ClaimRead[] | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    void listClaims().then((res) => {
      if (isNetworkError(res)) setError(true);
      else setClaims(res);
    });
  }, [refreshKey]);

  if (error && !claims) return <p className="text-sm text-caution">Couldn't load your claims.</p>;
  if (!claims) return <p className="text-sm text-muted">Loading…</p>;
  if (claims.length === 0) return <p className="text-sm text-muted">No claims yet. Claim a paper above.</p>;

  return (
    <ul className="flex flex-col gap-2">
      {claims.map((c) => (
        <li key={c.id}>
          <button
            onClick={() => onOpen(c)}
            className="flex w-full items-center justify-between gap-3 rounded-lg border border-hairline bg-white px-4 py-3 text-left shadow-sm transition hover:border-ink/20"
          >
            <span className="min-w-0 truncate font-mono text-sm text-ink">{c.paper_ref}</span>
            <span className="flex shrink-0 gap-3 text-xs text-muted">
              <Slot label="manuscript" filled={c.has_manuscript} />
              <Slot label="source" filled={c.has_source} />
            </span>
          </button>
        </li>
      ))}
    </ul>
  );
}

function Slot({ label, filled }: { label: string; filled: boolean }) {
  return (
    <span className="flex items-center gap-1">
      <span
        aria-hidden
        className={`inline-block h-2 w-2 rounded-full ${filled ? "bg-accent" : "border border-muted"}`}
      />
      {label}
    </span>
  );
}
