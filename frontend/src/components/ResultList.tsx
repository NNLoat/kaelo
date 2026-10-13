import type { PaperCard } from "../api/papers";
import ResultCard from "./ResultCard";
import { useScorePolling } from "./useScorePolling";

export default function ResultList({
  papers,
  onOpen,
}: {
  papers: PaperCard[];
  onOpen: (id: number) => void;
}) {
  const live = useScorePolling(papers);
  return (
    <div className="flex flex-col gap-4">
      {live.map((p) => (
        <ResultCard key={p.id} paper={p} onOpen={onOpen} />
      ))}
    </div>
  );
}
