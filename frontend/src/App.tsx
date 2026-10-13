import { useState } from "react";
import type { PaperCard } from "./api/papers";
import { AuthProvider, useAuth } from "./components/AuthProvider";
import AuthBar from "./components/AuthBar";
import LoginForm from "./components/LoginForm";
import RegisterForm from "./components/RegisterForm";
import SearchBox from "./components/SearchBox";
import ResultList from "./components/ResultList";
import PaperDetail from "./components/PaperDetail";

type View = { name: "search" } | { name: "detail"; id: number };

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

  return <Reader />;
}

function Reader() {
  const [papers, setPapers] = useState<PaperCard[]>([]);
  const [view, setView] = useState<View>({ name: "search" });

  if (view.name === "detail") {
    return (
      <div className="min-h-screen bg-paper text-ink">
        <div className="mx-auto max-w-3xl px-6 pt-6">
          <AuthBar />
        </div>
        <PaperDetail id={view.id} onBack={() => setView({ name: "search" })} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <AuthBar />

        <header className="mb-8">
          <p className="font-serif text-3xl text-ink">Kaelo</p>
          <p className="mt-1 text-muted">
            Search scientific papers and see how reproducible they are.
          </p>
        </header>

        <SearchBox onResults={setPapers} />

        {papers.length > 0 && (
          <div className="mt-8">
            <ResultList papers={papers} onOpen={(id) => setView({ name: "detail", id })} />
          </div>
        )}
      </div>
    </div>
  );
}
