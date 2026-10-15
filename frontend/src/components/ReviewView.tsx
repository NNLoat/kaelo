import { useState } from "react";
import Markdown from "react-markdown";
import { downloadArchive, isNetworkError, type GenerationRead } from "../api/codegen";

// Element styling for the rendered REVIEW.md. There is no typography plugin, so
// headings, lists, and paragraphs are styled here. Headings use the serif
// display face for a clear hierarchy; body sits on a readable <80ch measure.
const markdownComponents = {
  h1: (props: React.ComponentProps<"h1">) => (
    <h1 className="mt-8 mb-3 font-serif text-2xl text-ink first:mt-0" {...props} />
  ),
  h2: (props: React.ComponentProps<"h2">) => (
    <h2 className="mt-7 mb-2 font-serif text-xl text-ink first:mt-0" {...props} />
  ),
  h3: (props: React.ComponentProps<"h3">) => (
    <h3 className="mt-6 mb-2 font-serif text-lg text-ink first:mt-0" {...props} />
  ),
  p: (props: React.ComponentProps<"p">) => (
    <p className="my-3 leading-relaxed text-ink" {...props} />
  ),
  ul: (props: React.ComponentProps<"ul">) => (
    <ul className="my-3 ml-5 list-disc space-y-1.5 text-ink marker:text-muted" {...props} />
  ),
  ol: (props: React.ComponentProps<"ol">) => (
    <ol className="my-3 ml-5 list-decimal space-y-1.5 text-ink marker:text-muted" {...props} />
  ),
  li: (props: React.ComponentProps<"li">) => <li className="leading-relaxed" {...props} />,
  a: (props: React.ComponentProps<"a">) => (
    <a className="text-accent underline underline-offset-2 hover:text-accent-strong" {...props} />
  ),
  code: (props: React.ComponentProps<"code">) => (
    <code
      className="rounded bg-paper px-1.5 py-0.5 font-mono text-[0.85em] text-ink"
      {...props}
    />
  ),
  pre: (props: React.ComponentProps<"pre">) => (
    <pre
      className="my-4 overflow-auto rounded-md border border-hairline bg-paper p-4 font-mono text-xs leading-relaxed text-ink"
      {...props}
    />
  ),
  blockquote: (props: React.ComponentProps<"blockquote">) => (
    <blockquote className="my-4 border-l-2 border-hairline pl-4 text-muted" {...props} />
  ),
  hr: (props: React.ComponentProps<"hr">) => (
    <hr className="my-6 border-hairline" {...props} />
  ),
};

export default function ReviewView({ generation }: { generation: GenerationRead }) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const report = generation.files[0]?.content ?? "";

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
        <p className="text-sm font-medium text-ink">Reproducibility review</p>
        <button
          onClick={onDownload}
          disabled={downloading}
          className="rounded-md border border-accent px-3 py-1.5 text-sm font-medium text-accent transition hover:bg-accent hover:text-white focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {downloading ? "Preparing…" : "Download report"}
        </button>
      </div>
      {error && (
        <p role="alert" className="text-sm text-caution">
          {error}
        </p>
      )}

      <article className="max-w-[70ch] rounded-lg border border-hairline bg-white px-6 py-5 shadow-sm">
        <Markdown components={markdownComponents}>{report}</Markdown>
      </article>
    </div>
  );
}
