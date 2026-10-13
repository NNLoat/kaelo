import { useState } from "react";
import { useAuth } from "./AuthProvider";
import Field from "./Field";

export default function RegisterForm({ onSwitch }: { onSwitch: () => void }) {
  const { register } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const empty = !username || !password;

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (username.length < 3 || username.length > 32) {
      setError("Username needs 3 to 32 characters.");
      return;
    }
    if (password.length < 8 || password.length > 128) {
      setError("Password needs 8 to 128 characters.");
      return;
    }
    setBusy(true);
    const res = await register(username, password);
    setBusy(false);
    if (res.ok) return; // AuthProvider flips to authenticated state
    if (res.kind === "conflict") setError("That username is taken. Pick another.");
    else if (res.kind === "validation")
      setError(res.errors?.map((f) => f.message).join(" ") ?? "Check your username and password.");
    else setError("Can't reach the server. Try again.");
    setPassword("");
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-5" noValidate>
      <Field
        label="Username"
        value={username}
        onChange={setUsername}
        autoComplete="username"
        hint="3 to 32 characters."
      />
      <Field
        label="Password"
        type="password"
        value={password}
        onChange={setPassword}
        autoComplete="new-password"
        hint="8 to 128 characters."
      />
      {error && (
        <p role="alert" className="text-sm text-red-700">
          {error}
        </p>
      )}
      <button
        type="submit"
        disabled={empty || busy}
        className="rounded-md bg-accent px-4 py-2.5 font-medium text-white transition hover:bg-accent-strong focus-visible:ring-2 focus-visible:ring-accent/40 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {busy ? "Creating account…" : "Create account"}
      </button>
      <p className="text-sm text-muted">
        Already have an account?{" "}
        <button type="button" onClick={onSwitch} className="font-medium text-accent hover:underline">
          Sign in
        </button>
      </p>
    </form>
  );
}
