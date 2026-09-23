"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { api } from "@/lib/api";

type FollowUp = {
  id: number;
  sale_id: number;
  client_name: string | null;
  client_email: string | null;
  client_phone: string | null;
  product_title: string | null;
  variant_title: string | null;
  sold_at: string;
  planned_on: string;
  status: string;
  note: string | null;
  overdue: boolean;
};

export default function ClientesPage() {
  const [items, setItems] = useState<FollowUp[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    refresh();
  }, []);

  async function refresh() {
    setItems(await api<FollowUp[]>("/followups?status=pending"));
  }

  async function resolve(id: number, status: "done" | "skipped") {
    setBusy(true);
    try {
      await api(`/followups/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      });
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  const pending = items.filter((i) => i.status === "pending");

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 space-y-5 p-6">
        <header>
          <h1 className="text-2xl font-bold">Seguimiento post-venta</h1>
          <p className="text-sm text-slate-400">
            Contacta al cliente 15 días después de la compra para saber si quedó satisfecho.
          </p>
        </header>

        {pending.length === 0 ? (
          <p className="py-10 text-center text-sm text-slate-500">
            No hay clientes pendientes de contacto.
          </p>
        ) : (
          <ul className="space-y-3">
            {pending.map((f) => (
              <li
                key={f.id}
                className={`flex flex-wrap items-center gap-3 rounded-xl border p-4 ${
                  f.overdue
                    ? "border-rose-500/40 bg-rose-500/10"
                    : "border-slate-800 bg-slate-900"
                }`}
              >
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-white">
                    {f.client_name ?? f.client_email ?? "Cliente"}
                    {f.overdue && (
                      <span className="ml-2 rounded-full bg-rose-500/20 px-2 py-0.5 text-xs text-rose-300">
                        vencido
                      </span>
                    )}
                  </p>
                  <p className="truncate text-sm text-slate-400">
                    {f.client_email ?? "sin email"} · compró {f.product_title ?? "—"}
                    {f.variant_title ? ` (${f.variant_title})` : ""} el{" "}
                    {new Date(f.sold_at).toLocaleDateString("es")}
                  </p>
                </div>
                <div className="shrink-0 text-sm text-slate-300">
                  Contactar antes del{" "}
                  <span className="font-semibold text-emerald-400">
                    {new Date(f.planned_on).toLocaleDateString("es")}
                  </span>
                </div>
                <div className="shrink-0 space-x-2">
                  <button
                    onClick={() => resolve(f.id, "done")}
                    disabled={busy}
                    className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:opacity-40"
                  >
                    Hecho
                  </button>
                  <button
                    onClick={() => resolve(f.id, "skipped")}
                    disabled={busy}
                    className="rounded-lg bg-slate-700 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-slate-600 disabled:opacity-40"
                  >
                    Saltar
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}