export type Session = {
  access_token: string;
  token_type: string;
  seller: {
    id: number;
    email: string;
    full_name: string;
    role: string;
    monthly_target: number;
  };
};

const KEY = "session";

export function getSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

export function saveSession(session: Session) {
  window.localStorage.setItem(KEY, JSON.stringify(session));
}

export function clearSession() {
  window.localStorage.removeItem(KEY);
}