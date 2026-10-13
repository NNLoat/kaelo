import { useState } from "react";

// Two-step delete: a graphite text button that turns amber on confirm.
export default function ConfirmDelete({
  label,
  confirmLabel,
  onDelete,
}: {
  label: string;
  confirmLabel: string;
  onDelete: () => Promise<{ ok: boolean }>;
}) {
  const [armed, setArmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onConfirm() {
    setBusy(true);
    setError(null);
    const res = await onDelete();
    setBusy(false);
    setArmed(false);
    if (!res.ok) setError("That didn't delete. Try again.");
  }

  if (!armed) {
    return (
      <button
        onClick={() => setArmed(true)}
        className="text-sm text-muted transition hover:text-caution focus-visible:ring-2 focus-visible:ring-caution/40"
      >
        {label}
      </button>
    );
  }

  return (
    <span className="flex items-center gap-3 text-sm">
      <span className="text-caution">{confirmLabel}</span>
      <button
        onClick={onConfirm}
        disabled={busy}
        className="font-medium text-caution hover:underline disabled:opacity-50"
      >
        {busy ? "Deleting…" : "Delete"}
      </button>
      <button onClick={() => setArmed(false)} disabled={busy} className="text-muted hover:text-ink">
        Cancel
      </button>
      {error && (
        <span role="alert" className="text-caution">
          {error}
        </span>
      )}
    </span>
  );
}
