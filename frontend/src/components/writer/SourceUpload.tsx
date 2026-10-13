import { useRef, useState } from "react";
import { uploadSource, type SourceRead } from "../../api/writer";

const MAX_BYTES = 50 * 1024 * 1024; // mirror backend max_source_archive_bytes
const ARCHIVE_RE = /\.(zip|tar|tar\.gz|tgz|tar\.bz2|tar\.xz)$/i;

export default function SourceUpload({
  claimId,
  sourcePaths,
  onChange,
}: {
  claimId: string;
  sourcePaths: string[];
  onChange: (paths: string[]) => void;
}) {
  const [tab, setTab] = useState<"archive" | "git">("archive");
  const [gitUrl, setGitUrl] = useState("");
  const [skipped, setSkipped] = useState<number>(0);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const hasSource = sourcePaths.length > 0;

  function applyResult(src: SourceRead) {
    onChange(src.paths);
    setSkipped(src.skipped_paths.length);
  }

  async function onPickArchive(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    setError(null);
    if (!ARCHIVE_RE.test(file.name)) {
      setError("That isn't a zip or tar archive.");
      return;
    }
    if (file.size > MAX_BYTES) {
      setError("That archive is larger than 50 MB.");
      return;
    }
    await run(() => uploadSource(claimId, { file }));
  }

  async function onSubmitGit(e: React.FormEvent) {
    e.preventDefault();
    if (!gitUrl.trim()) return;
    setError(null);
    await run(() => uploadSource(claimId, { gitUrl: gitUrl.trim() }));
  }

  async function run(call: () => ReturnType<typeof uploadSource>) {
    setBusy(true);
    const res = await call();
    setBusy(false);
    if (res.ok) {
      applyResult(res.source);
      return;
    }
    if (res.kind === "too_large") setError("That source is over the size limit.");
    else if (res.kind === "unpack")
      setError(res.message ?? "That source couldn't be read. Check the archive or repository URL.");
    else setError("Upload failed. Try again.");
  }

  return (
    <div className="rounded-lg border border-hairline bg-white p-5 shadow-sm">
      <div className="flex items-center gap-2">
        <PresenceDot filled={hasSource} />
        <h3 className="text-sm font-semibold text-ink">Source code</h3>
      </div>

      <div className="mt-3 inline-flex rounded-md border border-hairline p-0.5" role="tablist" aria-label="Source input">
        {(["archive", "git"] as const).map((t) => (
          <button
            key={t}
            role="tab"
            aria-selected={tab === t}
            onClick={() => setTab(t)}
            className={`rounded px-3 py-1 text-sm transition ${
              tab === t ? "bg-accent text-white" : "text-muted hover:text-ink"
            }`}
          >
            {t === "archive" ? "Archive file" : "Git URL"}
          </button>
        ))}
      </div>

      <div className="mt-3">
        {tab === "archive" ? (
          <button
            onClick={() => inputRef.current?.click()}
            disabled={busy}
            className="rounded-md border border-accent px-3 py-1.5 text-sm font-medium text-accent transition hover:bg-accent hover:text-white focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Uploading…" : hasSource ? "Replace source" : "Upload source"}
          </button>
        ) : (
          <form onSubmit={onSubmitGit} className="flex gap-2">
            <input
              value={gitUrl}
              onChange={(e) => setGitUrl(e.target.value)}
              placeholder="https://github.com/owner/repo"
              className="flex-1 rounded-md border border-hairline px-3 py-2 text-sm text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
            />
            <button
              type="submit"
              disabled={!gitUrl.trim() || busy}
              className="rounded-md border border-accent px-3 py-1.5 text-sm font-medium text-accent transition hover:bg-accent hover:text-white focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? "Fetching…" : hasSource ? "Replace" : "Fetch"}
            </button>
          </form>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept=".zip,.tar,.tar.gz,.tgz,.tar.bz2,.tar.xz"
        onChange={onPickArchive}
        className="hidden"
      />

      {busy && <ProgressBar />}
      {error && (
        <p role="alert" className="mt-2 text-sm text-caution">
          {error}
        </p>
      )}

      {hasSource ? (
        <div className="mt-3">
          {skipped > 0 && (
            <p className="mb-1 text-xs text-muted">{skipped} binary files skipped.</p>
          )}
          <ul className="max-h-56 overflow-auto rounded border border-hairline">
            {sourcePaths.map((p) => (
              <li key={p} className="border-b border-hairline px-3 py-1 font-mono text-xs text-ink last:border-0">
                {p}
              </li>
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-3 text-sm text-muted">
          No source yet. Upload an archive or fetch a public repository.
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
