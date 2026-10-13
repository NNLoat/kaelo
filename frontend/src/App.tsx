import { useState } from "react";
import type { PaperCard } from "./api/papers";
import SearchBox from "./components/SearchBox";
import ResultList from "./components/ResultList";
import PaperDetail from "./components/PaperDetail";

type View = { name: "search" } | { name: "detail"; id: number };

export default function App() {
  const [papers, setPapers] = useState<PaperCard[]>([]);
  const [view, setView] = useState<View>({ name: "search" });

  if (view.name === "detail") {
    return (
      <div className="min-h-screen bg-paper text-ink">
        <PaperDetail id={view.id} onBack={() => setView({ name: "search" })} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <header className="mb-8">
          <p className="font-serif text-3xl text-ink">Kaelo</p>
          <p className="mt-1 text-muted">
            Search scientific papers and see how reproducible they are.
          </p>
        </header>

        <SearchBox onResults={setPapers} />

        {papers.length > 0 && (
          <div className="mt-8">
            <ResultList papers={papers} onOpen={(id) => setView({ name: "detail", id })} />
          </div>
        )}
      </div>
    </div>
  );
}
