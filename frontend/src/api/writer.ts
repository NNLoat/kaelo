const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface ClaimRead {
  id: string;
  paper_ref: string;
  paper_ref_normalized: string;
  has_manuscript: boolean;
  has_source: boolean;
  created_at: string;
}

export interface ManuscriptRead {
  filename: string;
  present: true;
}

export interface SourceRead {
  paths: string[];
  skipped_paths: string[];
}

export interface ClaimDetail extends ClaimRead {
  manuscript: ManuscriptRead | null;
  source_paths: string[];
}

export interface FieldError {
  field: string;
  rule: string;
  message: string;
}

export type NetworkError = { error: "network" };

export function isNetworkError(v: unknown): v is NetworkError {
  return typeof v === "object" && v !== null && "error" in v;
}

async function withTimeout<T>(ms: number, run: (signal: AbortSignal) => Promise<T>): Promise<T | NetworkError> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), ms);
  try {
    return await run(controller.signal);
  } catch {
    return { error: "network" };
  } finally {
    clearTimeout(timer);
  }
}

export async function createClaim(
  paperRef: string,
): Promise<
  { ok: true; claim: ClaimRead } | { ok: false; kind: "validation" | "network"; errors?: FieldError[] }
> {
  const res = await withTimeout(30_000, (signal) =>
    fetch(`${API_URL}/api/writer/claims`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ paper_ref: paperRef }),
      signal,
    }),
  );
  if (isNetworkError(res)) return { ok: false, kind: "network" };
  if (res.ok) return { ok: true, claim: await res.json() };
  if (res.status === 422) {
    const body = await res.json().catch(() => ({}));
    return { ok: false, kind: "validation", errors: body.detail };
  }
  return { ok: false, kind: "network" };
}

export function listClaims(): Promise<ClaimRead[] | NetworkError> {
  return withTimeout(30_000, async (signal) => {
    const res = await fetch(`${API_URL}/api/writer/claims`, { credentials: "include", signal });
    if (!res.ok) throw new Error();
    return (await res.json()) as ClaimRead[];
  });
}

export function getClaim(id: string): Promise<ClaimDetail | NetworkError> {
  return withTimeout(30_000, async (signal) => {
    const res = await fetch(`${API_URL}/api/writer/claims/${id}`, { credentials: "include", signal });
    if (!res.ok) throw new Error();
    return (await res.json()) as ClaimDetail;
  });
}

export async function uploadManuscript(
  id: string,
  file: File,
): Promise<
  { ok: true; manuscript: ManuscriptRead } | { ok: false; kind: "extract" | "too_large" | "network"; message?: string }
> {
  const form = new FormData();
  form.append("file", file);
  const res = await withTimeout(60_000, (signal) =>
    fetch(`${API_URL}/api/writer/claims/${id}/manuscript`, {
      method: "POST",
      credentials: "include",
      body: form,
      signal,
    }),
  );
  if (isNetworkError(res)) return { ok: false, kind: "network" };
  if (res.ok) return { ok: true, manuscript: await res.json() };
  if (res.status === 413) return { ok: false, kind: "too_large" };
  if (res.status === 422) {
    const body = await res.json().catch(() => ({}));
    return { ok: false, kind: "extract", message: detailMessage(body) };
  }
  return { ok: false, kind: "network" };
}

export async function uploadSource(
  id: string,
  input: { file: File } | { gitUrl: string },
): Promise<
  { ok: true; source: SourceRead } | { ok: false; kind: "unpack" | "too_large" | "network"; message?: string }
> {
  const form = new FormData();
  if ("file" in input) form.append("file", input.file);
  else form.append("git_url", input.gitUrl);
  const res = await withTimeout(120_000, (signal) =>
    fetch(`${API_URL}/api/writer/claims/${id}/source`, {
      method: "POST",
      credentials: "include",
      body: form,
      signal,
    }),
  );
  if (isNetworkError(res)) return { ok: false, kind: "network" };
  if (res.ok) return { ok: true, source: await res.json() };
  if (res.status === 413) return { ok: false, kind: "too_large" };
  if (res.status === 422) {
    const body = await res.json().catch(() => ({}));
    return { ok: false, kind: "unpack", message: detailMessage(body) };
  }
  return { ok: false, kind: "network" };
}

async function del(path: string): Promise<{ ok: boolean }> {
  const res = await withTimeout(30_000, (signal) =>
    fetch(`${API_URL}${path}`, { method: "DELETE", credentials: "include", signal }),
  );
  return { ok: !isNetworkError(res) && res.ok };
}

export const deleteManuscript = (id: string) => del(`/api/writer/claims/${id}/manuscript`);
export const deleteSource = (id: string) => del(`/api/writer/claims/${id}/source`);
export const deleteClaim = (id: string) => del(`/api/writer/claims/${id}`);

function detailMessage(body: unknown): string | undefined {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const d = (body as { detail: unknown }).detail;
    if (typeof d === "string") return d;
  }
  return undefined;
}
