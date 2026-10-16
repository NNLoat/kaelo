import { useState } from "react";
import type { PaperCard } from "./api/papers";
import type { GenerationRead } from "./api/codegen";
import { AuthProvider, useAuth } from "./components/AuthProvider";
import AuthBar from "./components/AuthBar";
import LoginForm from "./components/LoginForm";
import RegisterForm from "./components/RegisterForm";
import SearchBox from "./components/SearchBox";
import ResultList from "./components/ResultList";
import ResultSkeleton from "./components/ResultSkeleton";
import PaperDetail from "./components/PaperDetail";
import GenerationsList from "./components/GenerationsList";
import ArtifactView from "./components/ArtifactView";
import type { ClaimRead } from "./api/writer";
import ClaimForm from "./components/writer/ClaimForm";
import ClaimsList from "./components/writer/ClaimsList";
import ClaimWorkspace from "./components/writer/ClaimWorkspace";

type View =
  | { name: "search" }
  | { name: "detail"; id: number }
  | { name: "generations" }
  | { name: "artifact"; generation: GenerationRead };

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
            <p className="text-sm font-medium text-accent">Kaelo</p>
            <h1 className="mt-3 font-serif text-4xl leading-tight text-ink">
              Most papers don't reproduce. Find the ones that do.
            </h1>
            <p className="mt-5 text-lg leading-relaxed text-muted">
              Kaelo searches the literature, scores each paper's reproducibility, and generates the
              missing code when a repo isn't there.
            </p>
          </section>

          <section className="w-full max-w-sm justify-self-end">
            <h2 className="mb-5 text-xl font-semibold text-ink">
              {showRegister ? "Create your account" : "Sign in"}
            </h2>
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

  return <Authed />;
}

function Authed() {
  const { mode } = useAuth();
  return mode === "writer" ? <Writer /> : <Reader />;
}

function Writer() {
  const [selected, setSelected] = useState<ClaimRead | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <AuthBar />

        {selected ? (
          <ClaimWorkspace
            claimId={selected.id}
            onBack={() => {
              setSelected(null);
              setRefreshKey((k) => k + 1);
            }}
            onDeleted={() => {
              setSelected(null);
              setRefreshKey((k) => k + 1);
            }}
          />
        ) : (
          <>
            <header className="mb-8">
              <h1 className="font-serif text-3xl text-ink">Your workspace</h1>
              <p className="mt-1 text-muted">
                Add a paper you've written and upload its manuscript and code to evaluate its
                reproducibility.
              </p>
            </header>

            <div className="mb-8">
              <ClaimForm
                onClaimed={(c) => {
                  setSelected(c);
                  setRefreshKey((k) => k + 1);
                }}
              />
            </div>

            <ClaimsList refreshKey={refreshKey} onOpen={setSelected} />
          </>
        )}
      </div>
    </div>
  );
}

function Reader() {
  const [papers, setPapers] = useState<PaperCard[]>([]);
  const [searching, setSearching] = useState(false);
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

  if (view.name === "generations") {
    return (
      <div className="min-h-screen bg-paper text-ink">
        <div className="mx-auto max-w-3xl px-6 py-12">
          <AuthBar />
          <div className="mb-6 flex items-center justify-between">
            <h1 className="text-xl font-semibold text-ink">Your generations</h1>
            <button
              onClick={() => setView({ name: "search" })}
              className="text-sm text-accent hover:underline"
            >
              Back to search
            </button>
          </div>
          <GenerationsList onOpen={(g) => setView({ name: "artifact", generation: g })} />
        </div>
      </div>
    );
  }

  if (view.name === "artifact") {
    return (
      <div className="min-h-screen bg-paper text-ink">
        <div className="mx-auto max-w-3xl px-6 py-12">
          <AuthBar />
          <button
            onClick={() => setView({ name: "generations" })}
            className="mb-6 text-sm text-accent hover:underline"
          >
            Back to your generations
          </button>
          <ArtifactView generation={view.generation} />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <div className="mx-auto max-w-3xl px-6 py-12">
        <AuthBar />

        <header className="mb-8 flex items-start justify-between gap-4">
          <div>
            <h1 className="font-serif text-3xl text-ink">Discover</h1>
            <p className="mt-1 text-muted">
              Find research worth building on, and see how reproducible it is before you do.
            </p>
          </div>
          <button
            onClick={() => setView({ name: "generations" })}
            className="shrink-0 text-sm text-accent hover:underline"
          >
            Your generations
          </button>
        </header>

        <SearchBox onResults={setPapers} onLoadingChange={setSearching} />

        {searching ? (
          <div className="mt-8">
            <ResultSkeleton />
          </div>
        ) : (
          papers.length > 0 && (
            <div className="mt-8">
              <ResultList papers={papers} onOpen={(id) => setView({ name: "detail", id })} />
            </div>
          )
        )}
      </div>
    </div>
  );
}
