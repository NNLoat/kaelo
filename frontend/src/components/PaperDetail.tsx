import { useEffect, useState } from "react";
import { paper as fetchPaper, type PaperDetail as Detail } from "../api/papers";
import ScoreBar from "./ScoreBar";
import SourceBadges from "./SourceBadges";

type State =
  | { kind: "loading" }
  | { kind: "ready"; paper: Detail }
  | { kind: "not_found" }
  | { kind: "error" };

export default function PaperDetail({ id, onBack }: { id: number; onBack: () => void }) {
  const [state, setState] = useState<State>({ kind: "loading" });

  async function load() {
    setState({ kind: "loading" });
    const res = await fetchPaper(id);
    if (res.ok) setState({ kind: "ready", paper: res.paper });
    else setState({ kind: res.kind === "not_found" ? "not_found" : "error" });
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  return (
    <div className="mx-auto max-w-3xl px-6 py-10">
      <button
        onClick={onBack}
        className="mb-6 text-sm text-accent transition hover:underline focus-visible:ring-2 focus-visible:ring-accent/40"
      >
        Back to search
      </button>

      {state.kind === "loading" && <p className="text-muted">Loading…</p>}

      {state.kind === "not_found" && (
        <div>
          <p className="text-ink">That paper isn't in the cache.</p>
          <button onClick={onBack} className="mt-2 text-sm text-accent hover:underline">
            Return to search
          </button>
        </div>
      )}

      {state.kind === "error" && (
        <div>
          <p role="alert" className="text-red-700">
            Couldn't load this paper.
          </p>
          <button onClick={load} className="mt-2 text-sm text-accent hover:underline">
            Retry
          </button>
        </div>
      )}

      {state.kind === "ready" && <Body paper={state.paper} />}
    </div>
  );
}

function Body({ paper }: { paper: Detail }) {
  return (
    <article className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <h1 className="font-serif text-3xl leading-tight text-ink">{paper.title}</h1>
        {paper.authors.length > 0 && <p className="text-muted">{paper.authors.join(", ")}</p>}
        <div className="flex flex-wrap items-center gap-3">
          <SourceBadges sources={paper.sources} />
          {paper.published_date && (
            <span className="text-sm text-muted">Published {paper.published_date}</span>
          )}
        </div>
      </header>

      {paper.abstract && (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-ink">Abstract</h2>
          <p className="leading-relaxed text-ink">{paper.abstract}</p>
        </section>
      )}

      <section>
        <h2 className="mb-3 text-sm font-semibold text-ink">Scores</h2>
        <div className="grid gap-4 rounded-lg border border-hairline bg-white p-5 shadow-sm sm:grid-cols-3">
          <ScoreBar label="Relevance" cell={paper.relevance} />
          <ScoreBar label="Reproducibility" cell={paper.reproducibility} />
          <ScoreBar label="Final score" cell={paper.final} emphasis />
        </div>
        {paper.blurb && <p className="mt-3 text-sm leading-relaxed text-ink">{paper.blurb}</p>}
      </section>

      <section className="grid gap-6 sm:grid-cols-2">
        <div>
          <h2 className="mb-2 text-sm font-semibold text-ink">Repository</h2>
          {paper.repo_url ? (
            <a
              href={paper.repo_url}
              target="_blank"
              rel="noreferrer"
              className="break-all text-accent hover:underline"
            >
              {paper.repo_url}
            </a>
          ) : (
            <p className="text-sm text-muted">No repository associated with this paper.</p>
          )}
        </div>

        {paper.source_links.length > 0 && (
          <div>
            <h2 className="mb-2 text-sm font-semibold text-ink">Source links</h2>
            <ul className="flex flex-col gap-1">
              {paper.source_links.map((l) => (
                <li key={l.url}>
                  <a
                    href={l.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-accent capitalize hover:underline"
                  >
                    {l.source}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </section>

      <section>
        <h2 className="mb-2 text-sm font-semibold text-ink">Experiment setup</h2>
        {paper.experiment_setup?.available ? (
          <dl className="grid gap-2 text-sm text-ink sm:grid-cols-2">
            <Setup term="Hyperparameters" value={paper.experiment_setup.hyperparameters} />
            <Setup term="Datasets" value={paper.experiment_setup.datasets} />
            <Setup term="Environment" value={paper.experiment_setup.environment} />
          </dl>
        ) : (
          <p className="text-sm text-muted">Not yet available.</p>
        )}
      </section>

      <section>
        <button
          disabled
          title="Code generation is opt-in and handled by a separate feature."
          className="rounded-md border border-hairline px-4 py-2 text-sm text-muted disabled:cursor-not-allowed"
        >
          {paper.repo_url ? "Generate code review" : "Generate code"}
        </button>
        <p className="mt-1 text-xs text-muted">Off by default. Opt in from the code-generation tools.</p>
      </section>
    </article>
  );
}

function Setup({ term, value }: { term: string; value: string | null }) {
  return (
    <div>
      <dt className="text-muted">{term}</dt>
      <dd>{value ?? "—"}</dd>
    </div>
  );
}
