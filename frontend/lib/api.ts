import { clearSession, getSession } from "@/lib/auth";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const session = getSession();
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (session) headers["Authorization"] = `Bearer ${session.access_token}`;

  const res = await fetch(`${API_URL}/api/v1${path}`, {
    headers,
    ...init,
  });

  if (res.status === 401) {
    clearSession();
    if (typeof window !== "undefined" && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
  }

  if (!res.ok) {
    const body = await res.text();
    let detail = body;
    try {
      detail = (JSON.parse(body) as { detail?: string }).detail ?? body;
    } catch {
      detail = body;
    }
    throw new Error(detail);
  }
  return res.json();
}