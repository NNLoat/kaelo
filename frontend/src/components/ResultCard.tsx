import type { PaperCard } from "../api/papers";
import ScoreBar from "./ScoreBar";
import SourceBadges from "./SourceBadges";

export default function ResultCard({ paper, onOpen }: { paper: PaperCard; onOpen: (id: number) => void }) {
  return (
    <article className="rounded-lg border border-hairline bg-white p-5 shadow-sm transition hover:border-ink/20">
      <button
        onClick={() => onOpen(paper.id)}
        className="block w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent/40"
      >
        <h3 className="font-serif text-lg leading-snug text-ink">{paper.title}</h3>
      </button>

      {paper.authors.length > 0 && (
        <p className="mt-1 text-sm text-muted">{paper.authors.join(", ")}</p>
      )}

      <div className="mt-3">
        <SourceBadges sources={paper.sources} />
      </div>

      {paper.blurb && <p className="mt-3 text-sm leading-relaxed text-ink">{paper.blurb}</p>}

      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        <ScoreBar label="Relevance" cell={paper.relevance} />
        <ScoreBar label="Reproducibility" cell={paper.reproducibility} />
        <ScoreBar label="Overall" cell={paper.final} emphasis />
      </div>
    </article>
  );
}
