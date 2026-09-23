"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getSession, saveSession, type Session } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit() {
    if (!email.trim() || password.length < 8) {
      setError(mode === "register" ? "Contraseña de 8+ caracteres" : "Datos incompletos");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const body =
        mode === "register"
          ? JSON.stringify({ email, full_name: fullName, password })
          : JSON.stringify({ email, password });
      const session = await api<Session>(`/auth/${mode}`, {
        method: "POST",
        body,
      });
      saveSession(session);
      router.push("/");
      router.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setBusy(false);
    }
  }

  if (getSession()) {
    router.replace("/");
    return null;
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-950 p-6">
      <div className="w-full max-w-sm space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div>
          <h1 className="text-xl font-bold text-white">Shopify Manager</h1>
          <p className="text-sm text-slate-400">
            {mode === "login" ? "Inicia sesión como vendedor" : "Crea tu cuenta de vendedor"}
          </p>
        </div>

        <div className="grid grid-cols-2 text-center text-sm">
          {(["login", "register"] as const).map((m) => (
            <button
              key={m}
              onClick={() => setMode(m)}
              className={`border-b-2 pb-2 transition ${
                mode === m
                  ? "border-emerald-500 text-emerald-400"
                  : "border-transparent text-slate-400 hover:text-white"
              }`}
            >
              {m === "login" ? "Entrar" : "Registrarse"}
            </button>
          ))}
        </div>

        {mode === "register" && (
          <input
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            placeholder="Nombre completo"
            className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        )}
        <input
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email"
          type="email"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
        />
        <input
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="Contraseña"
          type="password"
          className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
        />

        {error && <p className="text-sm text-rose-400">{error}</p>}

        <button
          onClick={submit}
          disabled={busy}
          className="w-full rounded-lg bg-emerald-600 py-2.5 font-semibold text-white transition hover:bg-emerald-500 disabled:opacity-40"
        >
          {busy ? "Espera…" : mode === "login" ? "Entrar" : "Crear cuenta"}
        </button>

        <p className="text-center text-xs text-slate-500">
          Demo: ana@tienda.com · secret123
        </p>
      </div>
    </main>
  );
}