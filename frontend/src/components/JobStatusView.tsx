import { useEffect, useRef, useState } from "react";
import {
  getJob,
  getGeneration,
  cancelJob,
  isNetworkError,
  type GenerationRead,
  type JobRead,
} from "../api/codegen";
import ArtifactView from "./ArtifactView";

const MIN_INTERVAL = 1500;
const MAX_INTERVAL = 8000;

export default function JobStatusView({ job, onRetry }: { job: JobRead; onRetry: () => void }) {
  const [state, setState] = useState<JobRead>(job);
  const [generation, setGeneration] = useState<GenerationRead | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const interval = useRef(MIN_INTERVAL);

  useEffect(() => {
    setState(job);
    interval.current = MIN_INTERVAL;
  }, [job]);

  async function cancel() {
    setCancelling(true);
    const res = await cancelJob(state.id);
    setCancelling(false);
    if (!isNetworkError(res)) setState(res); // cancelled -> polling stops
  }

  // poll while the job is in flight (interval with backoff cap)
  useEffect(() => {
    if (state.state !== "pending" && state.state !== "running") return;
    const timer = setTimeout(async () => {
      const res = await getJob(state.id);
      if (!isNetworkError(res)) {
        setState(res);
        interval.current = Math.min(interval.current * 1.5, MAX_INTERVAL);
      }
    }, interval.current);
    return () => clearTimeout(timer);
  }, [state]);

  // once succeeded, load the generated artifact
  useEffect(() => {
    if (state.state !== "succeeded" || !state.generation_id) return;
    void getGeneration(state.generation_id).then((res) => {
      if (isNetworkError(res)) setLoadError(true);
      else setGeneration(res);
    });
  }, [state]);

  if (state.state === "pending" || state.state === "running") {
    return (
      <div className="flex items-center gap-3">
        <p className="text-sm text-muted" aria-live="polite">
          {state.state === "pending" ? "Queued…" : "Generating…"}
        </p>
        <button
          onClick={cancel}
          disabled={cancelling}
          className="text-sm font-medium text-caution hover:underline disabled:opacity-50"
        >
          {cancelling ? "Cancelling…" : "Cancel"}
        </button>
      </div>
    );
  }

  if (state.state === "cancelled") {
    return (
      <div>
        <p className="text-sm text-muted">Generation cancelled.</p>
        <button onClick={onRetry} className="mt-2 text-sm font-medium text-accent hover:underline">
          Start again
        </button>
      </div>
    );
  }

  if (state.state === "refused") {
    return (
      <p className="text-sm text-caution">
        {state.reason ?? "This generation can't run for this paper yet."}
      </p>
    );
  }

  if (state.state === "failed") {
    return (
      <div>
        <p role="alert" className="text-sm text-caution">
          {state.reason ? `Generation failed: ${state.reason}` : "Generation failed."}
        </p>
        <button onClick={onRetry} className="mt-2 text-sm font-medium text-accent hover:underline">
          Try again
        </button>
      </div>
    );
  }

  // succeeded
  if (loadError) {
    return (
      <p role="alert" className="text-sm text-caution">
        Couldn't load the generated code.
      </p>
    );
  }
  if (!generation) return <p className="text-sm text-muted">Loading result…</p>;
  return <ArtifactView generation={generation} />;
}
