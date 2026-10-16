import { useState } from "react";
import { createClaim, type ClaimRead } from "../../api/writer";

export default function ClaimForm({ onClaimed }: { onClaimed: (claim: ClaimRead) => void }) {
  const [ref, setRef] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!ref.trim()) return;
    setBusy(true);
    setError(null);
    const res = await createClaim(ref.trim());
    setBusy(false);
    if (res.ok) {
      onClaimed(res.claim); // opens the workspace (new or existing claim)
      setRef("");
      return;
    }
    if (res.kind === "validation")
      setError(res.errors?.map((f) => f.message).join(" ") ?? "That doesn't look like a paper reference.");
    else setError("Couldn't reach the server. Try again.");
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-2">
      <label htmlFor="paper-ref" className="text-sm font-medium text-ink">
        Add your paper
      </label>
      <div className="flex gap-2">
        <input
          id="paper-ref"
          value={ref}
          onChange={(e) => setRef(e.target.value)}
          placeholder="arXiv ID, DOI, or paper URL"
          className="flex-1 rounded-md border border-hairline bg-white px-3 py-2 text-ink outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
        />
        <button
          type="submit"
          disabled={!ref.trim() || busy}
          className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white transition hover:bg-accent-strong focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {busy ? "Adding…" : "Add paper"}
        </button>
      </div>
      {error && (
        <p role="alert" className="text-sm text-caution">
          {error}
        </p>
      )}
    </form>
  );
}
