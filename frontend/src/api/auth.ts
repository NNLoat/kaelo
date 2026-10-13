const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface UserRead {
  id: number;
  username: string;
}

export interface FieldError {
  field: string;
  rule: string;
  message: string;
}

async function post(path: string, body: unknown, timeoutMs: number) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(`${API_URL}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify(body),
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timer);
  }
}

export async function register(
  username: string,
  password: string,
): Promise<
  | { ok: true; user: UserRead }
  | { ok: false; kind: "conflict" | "validation" | "network"; errors?: FieldError[] }
> {
  try {
    const res = await post("/api/auth/register", { username, password }, 30_000);
    if (res.status === 201) return { ok: true, user: await res.json() };
    if (res.status === 409) return { ok: false, kind: "conflict" };
    if (res.status === 422) {
      const body = await res.json().catch(() => ({}));
      return { ok: false, kind: "validation", errors: body.detail };
    }
    return { ok: false, kind: "network" };
  } catch {
    return { ok: false, kind: "network" };
  }
}

export async function login(
  username: string,
  password: string,
): Promise<{ ok: true; user: UserRead } | { ok: false; kind: "invalid" | "network" }> {
  try {
    const res = await post("/api/auth/login", { username, password }, 30_000);
    if (res.ok) return { ok: true, user: await res.json() };
    if (res.status === 401 || res.status === 422) return { ok: false, kind: "invalid" };
    return { ok: false, kind: "network" };
  } catch {
    return { ok: false, kind: "network" };
  }
}

export async function logout(): Promise<{ ok: boolean }> {
  try {
    const res = await post("/api/auth/logout", {}, 10_000);
    return { ok: res.ok };
  } catch {
    return { ok: false };
  }
}

export async function me(): Promise<UserRead | null> {
  try {
    const res = await fetch(`${API_URL}/api/auth/me`, { credentials: "include" });
    return res.ok ? await res.json() : null;
  } catch {
    return null;
  }
}
