import { useState } from "react";
import { useAuth } from "./AuthProvider";
import Field from "./Field";

export default function LoginForm({ onSwitch }: { onSwitch: () => void }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!username || !password) {
      setError("Enter your username and password.");
      return;
    }
    setBusy(true);
    const res = await login(username, password);
    setBusy(false);
    if (res.ok) return;
    if (res.kind === "invalid") {
      setError("Username or password is incorrect.");
      setPassword("");
    } else {
      setError("Can't reach the server. Try again.");
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
      <Field label="Username" value={username} onChange={setUsername} autoComplete="username" />
      <Field
        label="Password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="current-password"
      />
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={busy}
        className="rounded-md bg-accent px-4 py-2.5 font-medium text-white transition hover:bg-accent-strong focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Signing in…" : "Sign in"}
      </button>
      <p className="text-sm text-muted">
        New here?{" "}
        <button type="button" onClick={onSwitch} className="font-medium text-accent hover:underline">
          Create an account
        </button>
      </p>
    </form>
  );
}
