import { useRef, useState } from "react";
import { uploadManuscript, type ManuscriptRead } from "../../api/writer";

const MAX_BYTES = 25 * 1024 * 1024; // mirror backend max_manuscript_bytes

export default function ManuscriptUpload({
  claimId,
  manuscript,
  onChange,
}: {
  claimId: string;
  manuscript: ManuscriptRead | null;
  onChange: (m: ManuscriptRead | null) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  async function onPick(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allow re-picking the same file
    if (!file) return;
    setError(null);

    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("That isn't a PDF. Export your manuscript as a PDF and try again.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("That PDF is larger than 25 MB. Try a smaller file.");
      return;
    }

    setBusy(true);
    const res = await uploadManuscript(claimId, file);
    setBusy(false);
    if (res.ok) {
      onChange(res.manuscript);
      return;
    }
    if (res.kind === "too_large") setError("That PDF is larger than 25 MB. Try a smaller file.");
    else if (res.kind === "extract")
      setError(res.message ?? "That file isn't a readable PDF, so there's no text to store.");
    else setError("Upload failed. Try again.");
  }

  return (
    <div className="rounded-lg border border-hairline bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <PresenceDot filled={!!manuscript} />
          <h3 className="text-sm font-semibold text-ink">Manuscript</h3>
        </div>
        <button
          onClick={() => inputRef.current?.click()}
          disabled={busy}
          className="rounded-md border border-accent px-3 py-1.5 text-sm font-medium text-accent transition hover:bg-accent hover:text-white focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? "Uploading…" : manuscript ? "Replace manuscript" : "Upload manuscript"}
        </button>
      </div>

      <input ref={inputRef} type="file" accept="application/pdf,.pdf" onChange={onPick} className="hidden" />

      <p className="mt-3 text-sm text-muted">
        {manuscript ? (
          <>
            Stored: <span className="font-mono text-ink">{manuscript.filename}</span>
          </>
        ) : (
          "No manuscript yet. Upload a PDF to extract its text."
        )}
      </p>

      {busy && <ProgressBar />}
      {error && (
        <p role="alert" className="mt-2 text-sm text-caution">
          {error}
        </p>
      )}
    </div>
  );
}

function PresenceDot({ filled }: { filled: boolean }) {
  return (
    <span
      aria-hidden
      className={`inline-block h-2.5 w-2.5 rounded-full ${filled ? "bg-accent" : "border border-muted"}`}
    />
  );
}

function ProgressBar() {
  return (
    <div className="mt-3 h-1 overflow-hidden rounded-full bg-hairline">
      <div className="h-full w-1/3 animate-pulse rounded-full bg-accent" />
    </div>
  );
}
