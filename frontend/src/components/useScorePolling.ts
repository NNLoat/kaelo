import { useEffect, useRef, useState } from "react";
import { scores as fetchScores, type PaperCard } from "../api/papers";

const INTERVAL_MS = 2000;
const MAX_ATTEMPTS = 60; // ~2 min bound, then give up polling

export type SortKey = "relevance" | "final";

function hasPending(cards: PaperCard[]): boolean {
  return cards.some(
    (c) =>
      c.relevance.status === "pending" ||
      c.reproducibility.status === "pending" ||
      c.final.status === "pending",
  );
}

// Rank value for a given sort key: ready scores first (desc); pending/unavailable last.
function rankBy(key: SortKey, c: PaperCard): number {
  const cell = key === "final" ? c.final : c.relevance;
  return cell.status === "ready" && cell.value != null ? cell.value : -1;
}

function sortCards(cards: PaperCard[], key: SortKey): PaperCard[] {
  return [...cards].sort((a, b) => rankBy(key, b) - rankBy(key, a));
}

// Takes the search's initial cards and the active sort key; returns a live copy
// whose pending score cells fill in via polling. The list is sorted on explicit
// events only — a new search or a sort-key change — never on a poll tick, so
// cards don't reshuffle under the reader while reproducibility scores stream in.
export function useScorePolling(initial: PaperCard[], sortKey: SortKey): PaperCard[] {
  const [cards, setCards] = useState<PaperCard[]>(() => sortCards(initial, sortKey));
  const attempts = useRef(0);

  // New search: reset and sort by the current key.
  useEffect(() => {
    setCards(sortCards(initial, sortKey));
    attempts.current = 0;
    // Only re-run on new results; a sort-key change is handled below so we don't
    // reset the polling budget just because the user re-sorted.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initial]);

  // Sort-key change: re-sort the current cards in place (keep streamed values).
  useEffect(() => {
    setCards((prev) => sortCards(prev, sortKey));
  }, [sortKey]);

  // Poll for pending scores, updating values in place WITHOUT re-sorting.
  useEffect(() => {
    if (!hasPending(cards) || attempts.current >= MAX_ATTEMPTS) return;

    const timer = setTimeout(async () => {
      attempts.current += 1;
      const ids = cards.map((c) => c.id);
      const updates = await fetchScores(ids);
      setCards((prev) =>
        prev.map((c) => {
          const u = updates[c.id];
          return u ? { ...c, ...u } : c;
        }),
      );
    }, INTERVAL_MS);

    return () => clearTimeout(timer);
  }, [cards]);

  return cards;
}
