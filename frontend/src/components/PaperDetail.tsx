import { useEffect, useState } from "react";
import {
  paper as fetchPaper,
  type CategoryScore,
  type Criterion,
  type Discrepancy,
  type PaperDetail as Detail,
  type ReproducibilityBreakdown,
} from "../api/papers";
import type { Case, JobRead } from "../api/codegen";
import { useAuth } from "./AuthProvider";
import ScoreBar from "./ScoreBar";
import SourceBadges from "./SourceBadges";
import GenerateButton from "./GenerateButton";
import JobStatusView from "./JobStatusView";

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
          <p role="alert" className="text-caution">
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
          <ScoreBar label="Overall" cell={paper.final} emphasis />
        </div>
        {paper.blurb && <p className="mt-3 text-sm leading-relaxed text-ink">{paper.blurb}</p>}

        {paper.reproducibility_breakdown && (
          <ReproBreakdown breakdown={paper.reproducibility_breakdown} />
        )}
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
        ) : paper.experiment_setup ? (
          <p className="text-sm text-muted">The experiment setup couldn't be extracted for this paper.</p>
        ) : (
          <p className="text-sm text-muted">Not yet available.</p>
        )}
      </section>

      <CodegenSection paper={paper} />
    </article>
  );
}

function CodegenSection({ paper }: { paper: Detail }) {
  const { mode } = useAuth();
  const [job, setJob] = useState<JobRead | null>(null);
  const [reviewJob, setReviewJob] = useState<JobRead | null>(null);

  const genCase: Case = mode === "writer" ? "writer" : paper.repo_url ? "align" : "generate";
  const paperRef = String(paper.id);

  return (
    <section className="flex flex-col gap-6">
      <div>
        <h2 className="mb-2 text-sm font-semibold text-ink">Code generation</h2>
        {job ? (
          <JobStatusView job={job} onRetry={() => setJob(null)} />
        ) : (
          <GenerateButton paperRef={paperRef} genCase={genCase} onStarted={setJob} />
        )}
      </div>

      <div>
        <h2 className="mb-2 text-sm font-semibold text-ink">Reproducibility review</h2>
        {reviewJob ? (
          <JobStatusView job={reviewJob} onRetry={() => setReviewJob(null)} />
        ) : (
          <GenerateButton paperRef={paperRef} genCase="review" onStarted={setReviewJob} />
        )}
      </div>
    </section>
  );
}

function ReproBreakdown({ breakdown }: { breakdown: ReproducibilityBreakdown }) {
  const criteria = breakdown.criteria ?? [];
  const categories = breakdown.categories ?? [];
  const discrepancies = breakdown.discrepancies ?? [];
  // Weakest angle first: order display categories by points lost, descending.
  const rankedCategories = [...categories].sort((a, b) => b.points_lost - a.points_lost);
  return (
    <div className="mt-4 rounded-lg border border-hairline bg-white p-5 shadow-sm">
      <h3 className="text-sm font-semibold text-ink">How the reproducibility score was reached</h3>
      {breakdown.standard_name && (
        <p className="mt-1 text-xs text-muted">
          Evaluated against {breakdown.standard_name}
          {breakdown.field_of_study && <> in {breakdown.field_of_study}</>}
        </p>
      )}
      {(breakdown.score_q != null || breakdown.score_d != null) && (
        <p className="mt-1 text-xs text-muted">
          {breakdown.score_q != null && <>Quality {breakdown.score_q.toFixed(2)}</>}
          {breakdown.score_q != null && breakdown.score_d != null && <> · </>}
          {breakdown.score_d != null && <>Agreement {breakdown.score_d.toFixed(2)}</>}
        </p>
      )}
      <div className="mt-3 grid gap-4 sm:grid-cols-2">
        <ScoreBar label="Code quality" cell={breakdown.code_quality} />
        <ScoreBar label="Setup completeness" cell={breakdown.setup_completeness} />
      </div>
      {!breakdown.repo_exists && (
        <p className="mt-3 text-sm text-muted">
          No code repository was found, which lowered the code-quality contribution.
        </p>
      )}
      {rankedCategories.length > 0 && (
        <div className="mt-5">
          <h4 className="text-xs font-semibold text-ink">Where this paper lost points</h4>
          <ul className="mt-3 flex flex-col gap-3">
            {rankedCategories.map((c) => (
              <CategoryRow key={c.category} category={c} />
            ))}
          </ul>
        </div>
      )}
      {criteria.length > 0 && (
        <ul className="mt-4 divide-y divide-hairline border-t border-hairline">
          {criteria.map((c) => (
            <CriterionRow key={c.id} criterion={c} />
          ))}
        </ul>
      )}
      {discrepancies.length > 0 && (
        <div className="mt-5 border-t border-hairline pt-4">
          <h4 className="text-xs font-semibold text-ink">Paper-to-code discrepancies</h4>
          <ul className="mt-3 flex flex-col gap-3">
            {discrepancies.map((d) => (
              <DiscrepancyRow key={`${d.criterion_id}-${d.reference}`} discrepancy={d} />
            ))}
          </ul>
        </div>
      )}
      {breakdown.explanation && (
        <p className="mt-3 text-sm leading-relaxed text-ink">{breakdown.explanation}</p>
      )}
    </div>
  );
}

// Strong ≥ 0.85, Fair 0.60–0.85, Weak < 0.60. Paired with a dot so status
// isn't carried by color alone.
function level(score: number): { label: string; dot: string; text: string } {
  if (score >= 0.85) return { label: "Strong", dot: "bg-accent", text: "text-accent-strong" };
  if (score >= 0.6) return { label: "Fair", dot: "bg-caution", text: "text-caution" };
  return { label: "Weak", dot: "bg-red-700", text: "text-red-700" };
}

function CategoryRow({ category }: { category: CategoryScore }) {
  const pct = Math.round(Math.min(1, Math.max(0, category.score)) * 100);
  const l = level(category.score);
  return (
    <li className="flex flex-col gap-1">
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-ink">{category.category}</span>
        <span className="flex items-center gap-2 text-xs">
          <span className={`inline-flex items-center gap-1.5 font-medium ${l.text}`}>
            <span aria-hidden="true" className={`h-2 w-2 rounded-full ${l.dot}`} />
            {l.label}
          </span>
          <span className="tabular-nums text-ink">{pct}%</span>
        </span>
      </div>
      <div className="h-1 overflow-hidden rounded-full bg-hairline">
        <div
          className="h-full rounded-full bg-ink/40 transition-[width]"
          style={{ width: `${pct}%` }}
        />
      </div>
    </li>
  );
}

function DiscrepancyRow({ discrepancy }: { discrepancy: Discrepancy }) {
  return (
    <li className="text-sm">
      <p className="text-ink">
        <span className="font-medium">{discrepancy.criterion_id}</span>
        <span className="text-muted"> — {discrepancy.reference}</span>
      </p>
      <p className="mt-0.5 text-muted">
        Paper says {discrepancy.paper_value ?? "—"}; code shows {discrepancy.code_value ?? "—"}.
      </p>
    </li>
  );
}

const STATUS: Record<Criterion["status"], { label: string; dot: string; text: string }> = {
  met: { label: "Met", dot: "bg-accent", text: "text-accent-strong" },
  partial: { label: "Partial", dot: "bg-caution", text: "text-caution" },
  unmet: { label: "Unmet", dot: "bg-red-700", text: "text-red-700" },
  not_applicable: { label: "Not applicable", dot: "bg-muted", text: "text-muted" },
};

function CriterionRow({ criterion }: { criterion: Criterion }) {
  const s = STATUS[criterion.status];
  return (
    <li className="flex items-start gap-3 py-3">
      <span
        className={`mt-0.5 inline-flex shrink-0 items-center gap-1.5 text-xs font-medium ${s.text}`}
      >
        <span aria-hidden="true" className={`h-2 w-2 rounded-full ${s.dot}`} />
        {s.label}
      </span>
      <div className="min-w-0">
        <p className="text-sm font-medium text-ink">{criterion.title}</p>
        {(criterion.category || criterion.tag) && (
          <p className="mt-0.5 flex flex-wrap items-center gap-1.5 text-xs text-muted">
            {criterion.tag && (
              <span className="rounded-full bg-hairline px-1.5 py-0.5 text-[11px] text-ink">
                {criterion.tag}
              </span>
            )}
            {criterion.category && <span>{criterion.category}</span>}
          </p>
        )}
        {criterion.evidence_note && (
          <p className="mt-0.5 text-sm leading-relaxed text-muted">{criterion.evidence_note}</p>
        )}
      </div>
    </li>
  );
}

function Setup({ term, value }: { term: string; value: string | null }) {
  return (
    <div>
      <dt className="text-muted">{term}</dt>
      <dd>{value ?? "Not provided"}</dd>
    </div>
  );
}
