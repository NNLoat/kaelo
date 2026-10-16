// Placeholder cards shown while a search is in flight. The shape mirrors
// ResultCard (title, authors, source badges, three score bars) so the layout
// doesn't jump when real results replace it. The `prefers-reduced-motion`
// rule in index.css disables the pulse for users who opt out.

function SkeletonCard() {
  return (
    <article className="rounded-lg border border-hairline bg-white p-5 shadow-sm">
      {/* title */}
      <div className="h-5 w-3/4 animate-pulse rounded bg-hairline" />
      {/* authors */}
      <div className="mt-2 h-4 w-1/3 animate-pulse rounded bg-hairline" />
      {/* source badges */}
      <div className="mt-3 flex gap-2">
        <div className="h-5 w-16 animate-pulse rounded-full bg-hairline" />
        <div className="h-5 w-14 animate-pulse rounded-full bg-hairline" />
      </div>
      {/* score bars */}
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i}>
            <div className="h-3 w-20 animate-pulse rounded bg-hairline" />
            <div className="mt-2 h-2 w-full animate-pulse rounded-full bg-hairline" />
          </div>
        ))}
      </div>
    </article>
  );
}

export default function ResultSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-busy="true"
      className="flex flex-col gap-4"
    >
      <span className="sr-only">Searching for papers…</span>
      {Array.from({ length: count }, (_, i) => (
        <SkeletonCard key={i} />
      ))}
    </div>
  );
}
