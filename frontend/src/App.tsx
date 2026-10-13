import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./components/AuthProvider";
import AuthBar from "./components/AuthBar";
import LoginForm from "./components/LoginForm";
import RegisterForm from "./components/RegisterForm";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

interface Item {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}

function Shell() {
  const { user, loading } = useAuth();
  const [showRegister, setShowRegister] = useState(false);

  if (loading) {
    return (
      <div className="min-h-screen bg-paper text-ink">
        <div className="mx-auto max-w-2xl px-6 py-12">
          <p className="text-muted">Loading…</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-paper text-ink">
        <div className="mx-auto grid min-h-screen max-w-5xl items-center gap-12 px-6 py-16 lg:grid-cols-2">
          <section className="max-w-md">
            <p className="font-serif text-4xl text-ink">Kaelo</p>
            <p className="mt-4 text-lg leading-relaxed text-ink">
              Find scientific papers, see how reproducible they are, and close the gap when the
              code is missing.
            </p>
            <p className="mt-3 text-sm leading-relaxed text-muted">
              Sign in as a Reader to search and evaluate others' work, or as a Writer to check the
              reproducibility of your own.
            </p>
          </section>

          <section className="w-full max-w-sm justify-self-end">
            <h1 className="mb-5 text-xl font-semibold text-ink">
              {showRegister ? "Create your account" : "Sign in"}
            </h1>
            <div className="rounded-lg border border-hairline bg-white p-6 shadow-sm">
              {showRegister ? (
                <RegisterForm onSwitch={() => setShowRegister(false)} />
              ) : (
                <LoginForm onSwitch={() => setShowRegister(true)} />
              )}
            </div>
          </section>
        </div>
      </div>
    );
  }

  return <Home />;
}

function Home() {
  const [items, setItems] = useState<Item[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function loadItems() {
    try {
      const res = await fetch(`${API_URL}/api/items`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setItems(await res.json());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load items");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadItems();
  }, []);

  async function addItem(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      const res = await fetch(`${API_URL}/api/items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, description: description || null }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setName("");
      setDescription("");
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create item");
    }
  }

  async function removeItem(id: number) {
    try {
      const res = await fetch(`${API_URL}/api/items/${id}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await loadItems();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete item");
    }
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto max-w-2xl px-6 py-12">
        <AuthBar />

        <form
          onSubmit={addItem}
          className="mb-8 flex flex-col gap-3 rounded-lg border border-hairline bg-white p-5 shadow-sm sm:flex-row"
        >
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Name"
            className="flex-1 rounded-md border border-hairline px-3 py-2 outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
          />
          <input
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Description (optional)"
            className="flex-1 rounded-md border border-hairline px-3 py-2 outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/20"
          />
          <button
            type="submit"
            className="rounded-md bg-accent px-4 py-2 font-medium text-white transition hover:bg-accent-strong focus-visible:ring-2 focus-visible:ring-accent/40"
          >
            Add
          </button>
        </form>

        {error && (
          <div className="mb-4 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-red-700">
            {error}
          </div>
        )}

        {loading ? (
          <p className="text-muted">Loading…</p>
        ) : items.length === 0 ? (
          <p className="text-muted">No items yet. Add one above.</p>
        ) : (
          <ul className="flex flex-col gap-2">
            {items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between rounded-lg border border-hairline bg-white px-4 py-3 shadow-sm"
              >
                <div>
                  <p className="font-medium">{item.name}</p>
                  {item.description && <p className="text-sm text-muted">{item.description}</p>}
                </div>
                <button
                  onClick={() => removeItem(item.id)}
                  className="rounded-md px-2 py-1 text-sm text-muted transition hover:bg-red-50 hover:text-red-600"
                  aria-label={`Delete ${item.name}`}
                >
                  Delete
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
