import { useState } from "react";
import { startJob, isNetworkError, type Case, type JobRead } from "../api/codegen";

const LABELS: Record<Case, string> = {
  generate: "Generate code",
  align: "Align code",
  writer: "Generate from upload",
  review: "Review manuscript & code",
};

export default function GenerateButton({
  paperRef,
  genCase,
  onStarted,
}: {
  paperRef: string;
  genCase: Case;
  onStarted: (job: JobRead) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onClick() {
    setBusy(true);
    setError(null);
    const res = await startJob(paperRef, genCase);
    setBusy(false);
    if (isNetworkError(res)) {
      setError("Couldn't start generation. Try again.");
      return;
    }
    onStarted(res);
  }

  return (
    <div>
      <button
        onClick={onClick}
        disabled={busy}
        className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-strong focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Starting…" : LABELS[genCase]}
      </button>
      <p className="mt-1 text-xs text-muted">
        Opt-in. Generated code is unverified and never executed.
      </p>
      {error && (
        <p role="alert" className="mt-2 text-sm text-caution">
          {error}
        </p>
      )}
    </div>
  );
}
