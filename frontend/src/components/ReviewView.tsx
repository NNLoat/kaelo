import {
  Children,
  isValidElement,
  useEffect,
  useMemo,
  useState,
  type ComponentProps,
  type ReactNode,
} from "react";
import Markdown from "react-markdown";
import { downloadArchive, isNetworkError, type GenerationRead } from "../api/codegen";

function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^\w\s-]/g, "")
    .trim()
    .replace(/\s+/g, "-");
}

type Section = { title: string; slug: string; body: string; count: number; tone: string };

// A review is an intro plus `##` sections (e.g. "Gaps and inconsistencies",
// "Recommended improvements"). `count` is the number of top-level list items.
// shortcut: tone is guessed from the heading text; a section the model words
// differently just gets the accent colour.
function parseReport(markdown: string): { intro: string; sections: Section[] } {
  const intro: string[] = [];
  const sections: Section[] = [];
  let current: { title: string; lines: string[] } | null = null;
  const flush = () => {
    if (!current) return;
    const body = current.lines.join("\n").trim();
    sections.push({
      title: current.title,
      slug: slugify(current.title),
      body,
      count: body.split("\n").filter((l) => /^([-*]|\d+\.)\s+/.test(l)).length,
      tone: /gap|inconsisten|issue|problem/i.test(current.title)
        ? "var(--color-caution)"
        : "var(--color-accent)",
    });
  };
  for (const line of markdown.split("\n")) {
    const h2 = /^##\s+(.+?)\s*$/.exec(line);
    if (h2) {
      flush();
      current = { title: h2[1], lines: [] };
    } else if (current) {
      current.lines.push(line);
    } else if (!/^#\s/.test(line)) {
      intro.push(line); // the `# Reproducibility Review` title is shown by the page itself
    }
  }
  flush();
  return { intro: intro.join("\n").trim(), sections };
}

// "**Title.** detail" -> the bold lead-in becomes the row title, the rest the detail.
function splitLead(children: ReactNode): { lead: ReactNode; rest: ReactNode[] } | null {
  const nodes = Children.toArray(children);
  let first = nodes[0];
  let rest = nodes.slice(1);
  if (isValidElement(first) && first.type === markdownComponents.p) {
    const inner = Children.toArray((first.props as { children?: ReactNode }).children);
    first = inner[0];
    rest = [...inner.slice(1), ...rest];
  }
  if (!isValidElement(first) || first.type !== "strong") return null;
  const lead = Children.toArray((first.props as { children?: ReactNode }).children).map((c) =>
    typeof c === "string" ? c.replace(/[.:]\s*$/, "") : c,
  );
  return { lead, rest };
}

// Element styling for the rendered report. Lists are a ledger: one row per
// finding with the title on the left and the explanation on the right, so the
// wide page is used instead of wrapping every sentence down a narrow column.
const markdownComponents = {
  h3: (props: ComponentProps<"h3">) => (
    <h3 className="mt-6 mb-2 font-serif text-lg text-ink first:mt-0" {...props} />
  ),
  p: ({ node: _node, ...props }: ComponentProps<"p"> & { node?: unknown }) => (
    <p className="my-3 max-w-[68ch] leading-relaxed text-ink" {...props} />
  ),
  ul: ({ node: _node, ...props }: ComponentProps<"ul"> & { node?: unknown }) => (
    <ul className="m-0 list-none p-0" {...props} />
  ),
  ol: ({ node: _node, ...props }: ComponentProps<"ol"> & { node?: unknown }) => (
    <ol className="m-0 list-none p-0" {...props} />
  ),
  li: ({ node: _node, children }: ComponentProps<"li"> & { node?: unknown }) => {
    const split = splitLead(children);
    const row = "border-t border-hairline py-4 first:border-t-0 first:pt-3";
    if (!split || split.rest.length === 0) {
      return <li className={`${row} max-w-[68ch] leading-relaxed text-ink`}>{children}</li>;
    }
    return (
      <li className={`${row} grid gap-x-8 gap-y-1 md:grid-cols-[13rem_minmax(0,1fr)]`}>
        <span className="font-medium text-ink">{split.lead}</span>
        <div className="max-w-[62ch] leading-relaxed text-ink [&_li]:block [&_li]:border-0 [&_li]:py-0 [&_ul]:my-2 [&_ul]:ml-4 [&_ul]:list-disc">
          {split.rest}
        </div>
      </li>
    );
  },
  a: ({ node: _node, ...props }: ComponentProps<"a"> & { node?: unknown }) => (
    <a className="text-accent underline underline-offset-2 hover:text-accent-strong" {...props} />
  ),
  code: ({ node: _node, ...props }: ComponentProps<"code"> & { node?: unknown }) => (
    <code
      className="rounded bg-white px-1.5 py-0.5 font-mono text-[0.85em] text-ink"
      {...props}
    />
  ),
  pre: ({ node: _node, ...props }: ComponentProps<"pre"> & { node?: unknown }) => (
    <pre
      className="my-4 overflow-auto rounded-md border border-hairline bg-white p-4 font-mono text-xs leading-relaxed text-ink"
      {...props}
    />
  ),
  blockquote: ({ node: _node, ...props }: ComponentProps<"blockquote"> & { node?: unknown }) => (
    <blockquote className="my-4 border-l-2 border-hairline pl-4 text-muted" {...props} />
  ),
  hr: ({ node: _node, ...props }: ComponentProps<"hr"> & { node?: unknown }) => (
    <hr className="my-6 border-hairline" {...props} />
  ),
};

// The inline result in the workspace: counts plus a way to the full report.
export function ReviewSummary({
  generation,
  onOpen,
}: {
  generation: GenerationRead;
  onOpen: () => void;
}) {
  const { sections } = useMemo(
    () => parseReport(generation.files[0]?.content ?? ""),
    [generation],
  );
  const counts = sections.filter((s) => s.count > 0).map((s) => `${s.title} (${s.count})`);
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-hairline bg-white px-4 py-3">
        <p className="text-sm text-ink">
          {counts.length > 0 ? counts.join(", ") : "Review ready."}
        </p>
        <button
          onClick={onOpen}
          className="rounded-md border border-accent px-3 py-1.5 text-sm font-medium text-accent transition hover:bg-accent hover:text-white focus-visible:ring-2 focus-visible:ring-accent/40"
        >
          Open full report
        </button>
      </div>
      <p className="text-xs text-caution">{generation.disclaimer}</p>
    </div>
  );
}

export default function ReviewView({ generation }: { generation: GenerationRead }) {
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [active, setActive] = useState<string | null>(null);
  const report = generation.files[0]?.content ?? "";
  const { intro, sections } = useMemo(() => parseReport(report), [report]);

  // Highlight the rail link of the section nearest the top of the viewport.
  useEffect(() => {
    const els = sections
      .map((s) => document.getElementById(s.slug))
      .filter((e): e is HTMLElement => e !== null);
    if (els.length === 0) return;
    const io = new IntersectionObserver(
      (entries) => {
        const hit = entries.find((e) => e.isIntersecting);
        if (hit) setActive(hit.target.id);
      },
      { rootMargin: "0px 0px -70% 0px" },
    );
    els.forEach((e) => io.observe(e));
    return () => io.disconnect();
  }, [sections]);

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
    <div className="flex flex-col gap-6">
      <div className="rounded-md border border-caution/40 bg-caution/10 px-4 py-2 text-sm text-caution">
        {generation.disclaimer}
      </div>

      <div className="grid grid-cols-[minmax(0,1fr)] gap-8 lg:grid-cols-[14rem_minmax(0,1fr)]">
        <aside className="flex flex-col gap-4 lg:sticky lg:top-6 lg:self-start">
          <p className="font-serif text-lg text-ink">Reproducibility review</p>
          {sections.length > 1 && (
            <nav aria-label="Report sections">
              <ul className="flex gap-x-5 gap-y-1 overflow-x-auto lg:flex-col">
                {sections.map((s) => (
                  <li key={s.slug}>
                    <a
                      href={`#${s.slug}`}
                      aria-current={active === s.slug ? "location" : undefined}
                      className={`flex justify-between gap-3 text-sm whitespace-nowrap underline-offset-2 hover:underline focus-visible:ring-2 focus-visible:ring-accent/40 lg:whitespace-normal ${
                        active === s.slug ? "font-medium text-accent" : "text-muted"
                      }`}
                    >
                      <span>{s.title}</span>
                      {s.count > 0 && <span>{s.count}</span>}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>
          )}
          <div>
            <button
              onClick={onDownload}
              disabled={downloading}
              className="rounded-md border border-accent px-3 py-1.5 text-sm font-medium text-accent transition hover:bg-accent hover:text-white focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {downloading ? "Preparing…" : "Download report"}
            </button>
            {error && (
              <p role="alert" className="mt-2 text-sm text-caution">
                {error}
              </p>
            )}
          </div>
        </aside>

        <article className="min-w-0">
          {intro && <Markdown components={markdownComponents}>{intro}</Markdown>}
          {sections.length === 0 && (
            <Markdown components={markdownComponents}>{report}</Markdown>
          )}
          {sections.map((s) => (
            <section
              key={s.slug}
              id={s.slug}
              style={{ borderTopColor: s.tone }}
              className="mt-8 scroll-mt-6 border-t-2 pt-4 first:mt-0"
            >
              <h2 className="mb-2 font-serif text-xl text-ink">{s.title}</h2>
              <Markdown components={markdownComponents}>{s.body}</Markdown>
            </section>
          ))}
        </article>
      </div>
    </div>
  );
}
