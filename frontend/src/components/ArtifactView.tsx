import { useState } from "react";
import { downloadArchive, isNetworkError, type GenerationRead } from "../api/codegen";

export default function ArtifactView({ generation }: { generation: GenerationRead }) {
  const files = generation.files;
  const [selected, setSelected] = useState(0);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const active = files[selected];

  async function onDownload() {
    setDownloading(true);
    setError(null);
    const res = await downloadArchive(generation.id);
    setDownloading(false);
    if (isNetworkError(res)) {
      setError("Download failed. Try again.");
      return;
    }
    const url = URL.createObjectURL(res);
    const a = document.createElement("a");
    a.href = url;
    a.download = `generation-${generation.id}.zip`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-md border border-caution/40 bg-caution/10 px-4 py-3 text-sm text-caution">
        {generation.disclaimer}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-ink">
          <span className="font-medium">Code quality</span>{" "}
          <span className="font-mono">{generation.code_quality_score.toFixed(2)}</span>
          <p className="mt-1 text-muted">{generation.code_quality_rationale}</p>
        </div>
        <button
          onClick={onDownload}
          disabled={downloading}
          className="rounded-md border border-accent px-3 py-1.5 text-sm font-medium text-accent transition hover:bg-accent hover:text-white focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {downloading ? "Preparing…" : "Download code"}
        </button>
      </div>
      {error && (
        <p role="alert" className="text-sm text-caution">
          {error}
        </p>
      )}

      <div className="grid grid-cols-[minmax(10rem,16rem)_1fr] overflow-hidden rounded-lg border border-hairline bg-white shadow-sm">
        <nav className="border-r border-hairline p-2" aria-label="Generated files">
          <ul className="flex flex-col">
            {files.map((f, i) => (
              <li key={f.path}>
                <button
                  onClick={() => setSelected(i)}
                  className={`w-full truncate rounded px-2 py-1.5 text-left font-mono text-xs transition ${
                    i === selected ? "bg-accent/10 text-ink" : "text-muted hover:text-ink"
                  }`}
                  title={f.path}
                >
                  {f.path}
                </button>
              </li>
            ))}
          </ul>
        </nav>
        <pre className="max-h-[32rem] overflow-auto p-4 font-mono text-xs leading-relaxed text-ink">
          {active?.content ?? ""}
        </pre>
      </div>
    </div>
  );
}
