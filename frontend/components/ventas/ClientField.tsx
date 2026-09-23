"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

type ClientHit = { id: number; email: string | null; full_name: string | null };

export function ClientField({
  value,
  onChange,
}: {
  value: string;
  onChange: (email: string) => void;
}) {
  const [query, setQuery] = useState(value);
  const [clients, setClients] = useState<ClientHit[]>([]);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (!query.trim()) {
      setClients([]);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        setClients(await api<ClientHit[]>(`/clients?q=${encodeURIComponent(query)}&limit=6`));
        setOpen(true);
      } catch {
        setClients([]);
      }
    }, 250);
  }, [query]);

  function pick(hit: ClientHit) {
    const email = hit.email ?? "";
    setQuery(email);
    onChange(email);
    setOpen(false);
  }

  return (
    <div className="relative">
      <input
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          onChange(e.target.value);
        }}
        onFocus={() => clients.length > 0 && setOpen(true)}
        placeholder="Cliente (nombre o email)…"
        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
      />
      {open && clients.length > 0 && (
        <ul className="absolute z-10 mt-2 w-full overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-2xl">
          {clients.map((hit) => (
            <li key={hit.id}>
              <button
                type="button"
                onClick={() => pick(hit)}
                className="block w-full px-3 py-2 text-left text-sm transition hover:bg-slate-800"
              >
                <span className="text-white">{hit.full_name ?? "Sin nombre"}</span>
                <span className="ml-2 text-xs text-slate-400">{hit.email ?? "sin email"}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}