import { useState } from "react";
import type { PaperCard } from "../api/papers";
import ResultCard from "./ResultCard";
import SortControl from "./SortControl";
import { useScorePolling, type SortKey } from "./useScorePolling";

export default function ResultList({
  papers,
  onOpen,
}: {
  papers: PaperCard[];
  onOpen: (id: number) => void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("relevance");
  const live = useScorePolling(papers, sortKey);
  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-muted">
          {live.length} {live.length === 1 ? "result" : "results"}
        </p>
        <SortControl value={sortKey} onChange={setSortKey} />
      </div>
      {live.map((p) => (
        <ResultCard key={p.id} paper={p} onOpen={onOpen} />
      ))}
    </div>
  );
}
