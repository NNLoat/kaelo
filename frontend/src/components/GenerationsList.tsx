import { useEffect, useState } from "react";
import {
  listGenerations,
  deleteGeneration,
  isNetworkError,
  type GenerationRead,
} from "../api/codegen";

const CASE_LABEL: Record<GenerationRead["case"], string> = {
  generate: "Generated",
  align: "Aligned",
  writer: "From upload",
};

export default function GenerationsList({ onOpen }: { onOpen: (g: GenerationRead) => void }) {
  const [items, setItems] = useState<GenerationRead[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    void listGenerations().then((res) => {
      if (isNetworkError(res)) setError("Couldn't load your generations.");
      else setItems(res);
    });
  }, []);

  async function onDelete(id: string) {
    setDeleting(id);
    setError(null);
    const res = await deleteGeneration(id);
    setDeleting(null);
    if (res.ok) setItems((prev) => prev?.filter((g) => g.id !== id) ?? null);
    else setError("Couldn't delete that generation. Try again.");
  }

  if (error && !items) return <p className="text-sm text-caution">{error}</p>;
  if (!items) return <p className="text-sm text-muted">Loading…</p>;
  if (items.length === 0) return <p className="text-sm text-muted">No generations yet.</p>;

  return (
    <div className="flex flex-col gap-2">
      {error && <p className="text-sm text-caution">{error}</p>}
      {items.map((g) => (
        <div
          key={g.id}
          className="flex items-center justify-between gap-3 rounded-lg border border-hairline bg-white px-4 py-3 shadow-sm"
        >
          <button onClick={() => onOpen(g)} className="min-w-0 flex-1 text-left">
            <span className="font-medium text-ink">{CASE_LABEL[g.case]}</span>
            <span className="ml-2 truncate text-sm text-muted">{g.paper_ref}</span>
            {g.is_latest && (
              <span className="ml-2 rounded border border-accent/40 px-1.5 py-0.5 text-xs text-accent">
                latest
              </span>
            )}
          </button>
          <button
            onClick={() => onDelete(g.id)}
            disabled={deleting === g.id}
            className="rounded-md px-2 py-1 text-sm text-muted transition hover:bg-caution/10 hover:text-caution disabled:opacity-50"
            aria-label={`Delete ${CASE_LABEL[g.case]} generation for ${g.paper_ref}`}
          >
            {deleting === g.id ? "Deleting…" : "Delete"}
          </button>
        </div>
      ))}
    </div>
  );
}
