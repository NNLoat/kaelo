import { useRef, useState } from "react";
import { search, type PaperCard } from "../api/papers";

type Status =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "empty" }
  | { kind: "error"; message: string };

export default function SearchBox({
  onResults,
  onLoadingChange,
}: {
  onResults: (papers: PaperCard[]) => void;
  onLoadingChange?: (loading: boolean) => void;
}) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const inFlight = useRef<AbortController | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;

    inFlight.current?.abort(); // abandon the previous search (R1.7)
    const controller = new AbortController();
    inFlight.current = controller;

    setStatus({ kind: "loading" });
    onLoadingChange?.(true);
    const res = await search(q, controller.signal);
    if (controller.signal.aborted) return; // a newer search superseded this one
    onLoadingChange?.(false);

    if (res.ok) {
      setStatus({ kind: "idle" });
      onResults(res.papers);
      return;
    }
    onResults([]);
    if (res.kind === "empty") setStatus({ kind: "empty" });
    else if (res.kind === "validation")
      setStatus({ kind: "error", message: "Enter a query of 1 to 512 characters." });
    else if (res.kind === "source_failure")
      setStatus({ kind: "error", message: "The paper sources are unavailable right now. Try again." });
    else setStatus({ kind: "error", message: "Search couldn't complete. Try again." });
  }

  const loading = status.kind === "loading";

  return (
    <div>
      <form onSubmit={onSubmit} className="flex gap-2">
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search papers by topic, method, or keyword"
          maxLength={512}
          className="flex-1 rounded-md border border-hairline bg-white px-4 py-2.5 text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
        />
        <button
          type="submit"
          disabled={!query.trim() || loading}
          className="rounded-md bg-accent px-5 py-2.5 font-medium text-white transition hover:bg-accent-strong focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </form>

      {status.kind === "empty" && (
        <p className="mt-4 text-sm text-muted">No papers found. Try a different query.</p>
      )}
      {status.kind === "error" && (
        <p role="alert" className="mt-4 text-sm text-caution">
          {status.message}
        </p>
      )}
    </div>
  );
}
