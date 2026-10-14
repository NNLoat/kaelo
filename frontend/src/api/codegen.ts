const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type Case = "generate" | "align" | "writer";
export type JobState = "pending" | "running" | "succeeded" | "failed" | "refused" | "cancelled";

export interface JobRead {
  id: string;
  paper_ref: string;
  case: Case;
  state: JobState;
  reason: string | null;
  generation_id: string | null;
}

export interface GenFile {
  path: string;
  content: string;
}

export interface GenerationRead {
  id: string;
  paper_ref: string;
  case: Case;
  files: GenFile[];
  code_quality_score: number;
  code_quality_rationale: string;
  disclaimer: string;
  is_latest: boolean;
  created_at: string;
}

export type NetworkError = { error: "network" };

function isError(v: unknown): v is NetworkError {
  return typeof v === "object" && v !== null && "error" in v;
}
export { isError as isNetworkError };

async function req<T>(path: string, init: RequestInit, timeoutMs = 30_000): Promise<T | NetworkError> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(`${API_URL}${path}`, {
      credentials: "include",
      signal: controller.signal,
      ...init,
    });
    if (!res.ok) return { error: "network" };
    return (await res.json()) as T;
  } catch {
    return { error: "network" };
  } finally {
    clearTimeout(timer);
  }
}

export function startJob(paperRef: string, c: Case): Promise<JobRead | NetworkError> {
  return req<JobRead>("/api/codegen/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ paper_ref: paperRef, case: c }),
  });
}

export function getJob(id: string): Promise<JobRead | NetworkError> {
  return req<JobRead>(`/api/codegen/jobs/${id}`, {});
}

export function cancelJob(id: string): Promise<JobRead | NetworkError> {
  return req<JobRead>(`/api/codegen/jobs/${id}/cancel`, { method: "POST" });
}

export function getGeneration(id: string): Promise<GenerationRead | NetworkError> {
  return req<GenerationRead>(`/api/codegen/generations/${id}`, {});
}

export function listGenerations(): Promise<GenerationRead[] | NetworkError> {
  return req<GenerationRead[]>("/api/codegen/generations", {});
}

export async function downloadArchive(id: string): Promise<Blob | NetworkError> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30_000);
  try {
    const res = await fetch(`${API_URL}/api/codegen/generations/${id}/archive`, {
      credentials: "include",
      signal: controller.signal,
    });
    if (!res.ok) return { error: "network" };
    return await res.blob();
  } catch {
    return { error: "network" };
  } finally {
    clearTimeout(timer);
  }
}

export async function deleteGeneration(id: string): Promise<{ ok: boolean }> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30_000);
  try {
    const res = await fetch(`${API_URL}/api/codegen/generations/${id}`, {
      method: "DELETE",
      credentials: "include",
      signal: controller.signal,
    });
    return { ok: res.ok };
  } catch {
    return { ok: false };
  } finally {
    clearTimeout(timer);
  }
}
