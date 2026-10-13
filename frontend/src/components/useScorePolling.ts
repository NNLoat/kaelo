import { useEffect, useRef, useState } from "react";
import { scores as fetchScores, type PaperCard } from "../api/papers";

const INTERVAL_MS = 2000;
const MAX_ATTEMPTS = 60; // ~2 min bound, then give up polling

function hasPending(cards: PaperCard[]): boolean {
  return cards.some(
    (c) =>
      c.relevance.status === "pending" ||
      c.reproducibility.status === "pending" ||
      c.final.status === "pending",
  );
}

function finalRank(c: PaperCard): number {
  // computed Final Scores first (desc); pending/unavailable sort last
  return c.final.status === "ready" && c.final.value != null ? c.final.value : -1;
}

// Takes the search's initial cards; returns a live copy whose pending score
// cells fill in via polling, re-sorted when a Final Score resolves (R2.7, R5.5).
export function useScorePolling(initial: PaperCard[]): PaperCard[] {
  const [cards, setCards] = useState(initial);
  const attempts = useRef(0);

  useEffect(() => {
    setCards(initial);
    attempts.current = 0;
  }, [initial]);

  useEffect(() => {
    if (!hasPending(cards) || attempts.current >= MAX_ATTEMPTS) return;

    const timer = setTimeout(async () => {
      attempts.current += 1;
      const ids = cards.map((c) => c.id);
      const updates = await fetchScores(ids);
      setCards((prev) => {
        const next = prev.map((c) => {
          const u = updates[c.id];
          return u ? { ...c, ...u } : c;
        });
        return [...next].sort((a, b) => finalRank(b) - finalRank(a));
      });
    }, INTERVAL_MS);

    return () => clearTimeout(timer);
  }, [cards]);

  return cards;
}
