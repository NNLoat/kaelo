const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type ScoreStatus = "pending" | "ready" | "unavailable";

export interface ScoreCell {
  status: ScoreStatus;
  value: number | null;
}

export interface SourceBadge {
  source: string;
}

export interface PaperCard {
  id: number;
  title: string;
  authors: string[];
  sources: string[];
  relevance: ScoreCell;
  reproducibility: ScoreCell;
  final: ScoreCell;
  blurb: string | null;
}

export interface ExperimentSetup {
  hyperparameters: string | null;
  datasets: string | null;
  environment: string | null;
  available: boolean;
}

export interface ReproducibilityBreakdown {
  code_quality: ScoreCell;
  setup_completeness: ScoreCell;
  repo_exists: boolean;
  explanation: string | null;
}

export interface PaperDetail extends PaperCard {
  abstract: string | null;
  published_date: string | null;
  source_links: { source: string; url: string }[];
  repo_url: string | null;
  experiment_setup: ExperimentSetup | null;
  // null until reproducibility-scoring has run; existing reads unaffected (R8.1)
  reproducibility_breakdown: ReproducibilityBreakdown | null;
}

type ScoreUpdate = Pick<PaperCard, "relevance" | "reproducibility" | "final" | "blurb">;

function timed(ms: number) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  return { signal: controller.signal, done: () => clearTimeout(timer) };
}

// 30s timeout (R1.3/R1.6); the caller passes a shared signal so a new search
// abandons the previous in-flight call (R1.7).
export async function search(
  query: string,
  signal?: AbortSignal,
): Promise<
  | { ok: true; papers: PaperCard[] }
  | { ok: false; kind: "empty" | "source_failure" | "validation" | "network" }
> {
  const t = timed(30_000);
  const merged = mergeSignals(signal, t.signal);
  try {
    const res = await fetch(`${API_URL}/api/papers/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ query }),
      signal: merged,
    });
    if (res.ok) {
      const body = await res.json();
      const papers: PaperCard[] = body.papers ?? [];
      if (papers.length === 0) return { ok: false, kind: "empty" };
      return { ok: true, papers };
    }
    if (res.status === 422) return { ok: false, kind: "validation" };
    if (res.status === 502) return { ok: false, kind: "source_failure" };
    return { ok: false, kind: "network" };
  } catch {
    return { ok: false, kind: "network" };
  } finally {
    t.done();
  }
}

export async function scores(ids: number[]): Promise<Record<number, ScoreUpdate>> {
  if (ids.length === 0) return {};
  try {
    const res = await fetch(`${API_URL}/api/papers/scores?ids=${ids.join(",")}`, {
      credentials: "include",
    });
    return res.ok ? await res.json() : {};
  } catch {
    return {};
  }
}

// 30s timeout (R3.7)
export async function paper(
  id: number,
): Promise<{ ok: true; paper: PaperDetail } | { ok: false; kind: "not_found" | "network" }> {
  const t = timed(30_000);
  try {
    const res = await fetch(`${API_URL}/api/papers/${id}`, {
      credentials: "include",
      signal: t.signal,
    });
    if (res.ok) return { ok: true, paper: await res.json() };
    if (res.status === 404) return { ok: false, kind: "not_found" };
    return { ok: false, kind: "network" };
  } catch {
    return { ok: false, kind: "network" };
  } finally {
    t.done();
  }
}

// Abort when either signal aborts (timeout OR a newer search). Native
// AbortSignal.any isn't in our TS lib target, so wire it by hand.
function mergeSignals(a: AbortSignal | undefined, b: AbortSignal): AbortSignal {
  if (!a) return b;
  const controller = new AbortController();
  const forward = () => controller.abort();
  if (a.aborted || b.aborted) controller.abort();
  a.addEventListener("abort", forward);
  b.addEventListener("abort", forward);
  return controller.signal;
}
