import { useState } from "react";
import { useAuth } from "./AuthProvider";

export default function AuthBar() {
  const { user, mode, setMode, logout } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onLogout() {
    setBusy(true);
    setError(null);
    const res = await logout();
    setBusy(false);
    if (!res.ok) setError("Couldn't sign you out. Try again.");
    // on success AuthProvider clears the user and the app shows the login view
  }

  return (
    <div className="mb-10 border-b border-hairline pb-5">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-baseline gap-2">
          <span className="font-serif text-lg text-ink">Kaelo</span>
          <span className="text-sm text-muted">signed in as {user?.username}</span>
        </div>
        <div className="flex items-center gap-3">
          <div
            role="group"
            aria-label="Mode"
            className="inline-flex rounded-md border border-hairline bg-white p-0.5"
          >
            {(["reader", "writer"] as const).map((m) => (
              <button
                key={m}
                aria-pressed={mode === m}
                onClick={() => setMode(m)}
                className={`rounded px-3 py-1 text-sm capitalize transition focus-visible:ring-2 focus-visible:ring-accent/40 ${
                  mode === m ? "bg-accent text-white" : "text-muted hover:text-ink"
                }`}
              >
                {m}
              </button>
            ))}
          </div>
          <button
            onClick={onLogout}
            disabled={busy}
            className="rounded-md border border-hairline px-3 py-1 text-sm text-ink transition hover:border-ink/30 focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? "Signing out…" : "Sign out"}
          </button>
        </div>
      </div>
      {error && (
        <p role="alert" className="mt-2 text-sm text-caution">
          {error}
        </p>
      )}
    </div>
  );
}
