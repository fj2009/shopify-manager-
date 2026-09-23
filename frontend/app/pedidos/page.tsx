"use client";

import { useEffect, useState } from "react";
import { Sidebar } from "@/components/Sidebar";
import { api } from "@/lib/api";

type SaleItem = {
  id: number;
  shopify_order_id: string | null;
  quantity: number;
  unit_price: string;
  total: string;
  status: string;
  sold_at: string;
  client_email: string | null;
  client_name: string | null;
  product_title: string | null;
  variant_title: string | null;
  sku: string | null;
  image_url: string | null;
};

type Note = { id: number; author: string; specification: string; created_at: string };
type Event = { id: number; from_status: string | null; to_status: string; actor: string | null; created_at: string };
type Detail = {
  sale: SaleItem;
  client: { email: string | null; full_name: string | null; phone: string | null };
  product: { title: string; variant_title: string | null; sku: string | null; image_url: string | null };
  notes: Note[];
  events: Event[];
};

const STATUSES = ["pending", "workshop", "shipped", "delivered", "cancelled"];
const FLOW: Record<string, string[]> = {
  pending: ["workshop", "shipped", "delivered", "cancelled"],
  workshop: ["pending", "shipped", "delivered", "cancelled"],
  shipped: ["delivered", "cancelled"],
  delivered: [],
  cancelled: [],
};

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-slate-700 text-slate-200",
  workshop: "bg-amber-500/20 text-amber-300",
  shipped: "bg-sky-500/20 text-sky-300",
  delivered: "bg-emerald-500/20 text-emerald-300",
  cancelled: "bg-rose-500/20 text-rose-300",
};

function Chip({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[status] ?? "bg-slate-700 text-slate-200"}`}>
      {status}
    </span>
  );
}

export default function PedidosPage() {
  const [items, setItems] = useState<SaleItem[]>([]);
  const [filter, setFilter] = useState<string>("");
  const [selected, setSelected] = useState<Detail | null>(null);
  const [noteText, setNoteText] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    loadList();
  }, []);

  async function loadList() {
    const query = filter ? `?status=${filter}` : "";
    setItems(await api<SaleItem[]>(`/sales${query}`));
  }

  async function open(id: number) {
    setSelected(await api<Detail>(`/sales/${id}`));
  }

  async function transition(status: string) {
    if (!selected) return;
    setBusy(true);
    try {
      setSelected(
        await api<Detail>(`/sales/${selected.sale.id}/status`, {
          method: "PATCH",
          body: JSON.stringify({ status, actor: "vendedor" }),
        })
      );
      await loadList();
    } finally {
      setBusy(false);
    }
  }

  async function addNote() {
    if (!selected || !noteText.trim()) return;
    setBusy(true);
    try {
      await api(`/sales/${selected.sale.id}/notes`, {
        method: "POST",
        body: JSON.stringify({ author: "vendedor", specification: noteText }),
      });
      setSelected(await api<Detail>(`/sales/${selected.sale.id}`));
      setNoteText("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 space-y-5 p-6">
        <header className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Pedidos y taller</h1>
          <div className="flex gap-2">
            {["", ...STATUSES].map((s) => (
              <button
                key={s || "all"}
                onClick={() => {
                  setFilter(s);
                  loadList();
                }}
                className={`rounded-full px-3 py-1 text-xs transition ${
                  filter === s
                    ? "bg-emerald-600 text-white"
                    : "bg-slate-800 text-slate-300 hover:bg-slate-700"
                }`}
              >
                {s || "todos"}
              </button>
            ))}
          </div>
        </header>

        <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
          <section className="space-y-2">
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => open(item.id)}
                className={`w-full rounded-xl border p-4 text-left transition hover:bg-slate-900 ${
                  selected?.sale.id === item.id
                    ? "border-emerald-600 bg-slate-900"
                    : "border-slate-800 bg-slate-900/50"
                }`}
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="truncate font-medium text-white">
                      #{item.id} · {item.product_title ?? "—"}
                    </p>
                    <p className="truncate text-sm text-slate-400">
                      {item.client_name ?? item.client_email ?? "Cliente"} ·{" "}
                      {item.variant_title ?? ""} · {new Date(item.sold_at).toLocaleDateString("es")}
                    </p>
                  </div>
                  <div className="flex shrink-0 flex-col items-end gap-1">
                    <Chip status={item.status} />
                    <span className="text-sm font-semibold text-emerald-400">
                      ${Number(item.total).toFixed(2)}
                    </span>
                  </div>
                </div>
              </button>
            ))}
            {items.length === 0 && (
              <p className="py-10 text-center text-sm text-slate-500">Sin pedidos.</p>
            )}
          </section>

          {selected && (
            <section className="space-y-4 rounded-xl border border-slate-800 bg-slate-900 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-lg font-semibold text-white">Pedido #{selected.sale.id}</h2>
                  <p className="text-sm text-slate-400">
                    {selected.product.title}
                    {selected.product.variant_title ? ` · ${selected.product.variant_title}` : ""}
                  </p>
                </div>
                <Chip status={selected.sale.status} />
              </div>

              <div className="text-sm text-slate-300">
                <p>Cliente: {selected.client.full_name ?? "—"}</p>
                <p>Email: {selected.client.email ?? "—"}</p>
                {selected.sale.shopify_order_id && (
                  <p className="text-xs text-slate-500">Shopify: {selected.sale.shopify_order_id}</p>
                )}
              </div>

              <div>
                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
                  Especificaciones de taller
                </h3>
                {selected.notes.length === 0 ? (
                  <p className="text-sm text-slate-500">Sin notas.</p>
                ) : (
                  <ul className="space-y-2">
                    {selected.notes.map((n) => (
                      <li key={n.id} className="rounded-lg bg-slate-800/60 p-2 text-sm text-slate-200">
                        <span className="font-medium text-emerald-400">{n.author}</span>
                        <p className="mt-0.5 whitespace-pre-wrap">{n.specification}</p>
                      </li>
                    ))}
                  </ul>
                )}
                <div className="mt-2 flex gap-2">
                  <input
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Nueva especificación…"
                    className="flex-1 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
                  />
                  <button
                    onClick={addNote}
                    disabled={busy || !noteText.trim()}
                    className="rounded-lg bg-slate-700 px-3 py-2 text-sm font-medium text-white transition hover:bg-slate-600 disabled:opacity-40"
                  >
                    Añadir
                  </button>
                </div>
              </div>

              <div>
                <h3 className="mb-2 text-xs font-medium uppercase tracking-wide text-slate-400">
                  Historial
                </h3>
                <ol className="space-y-1 border-l border-slate-700 pl-3 text-sm">
                  {selected.events.map((e) => (
                    <li key={e.id} className="text-slate-300">
                      <span className="text-slate-400">
                        {new Date(e.created_at).toLocaleString("es")}
                      </span>{" "}
                      → {e.to_status}
                      {e.actor ? ` · por ${e.actor}` : ""}
                    </li>
                  ))}
                  <li className="text-slate-500">Creación → pending</li>
                </ol>
              </div>

              {FLOW[selected.sale.status]?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {FLOW[selected.sale.status].map((next) => (
                    <button
                      key={next}
                      onClick={() => transition(next)}
                      disabled={busy}
                      className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-500 disabled:opacity-40"
                    >
                      Marcar {next}
                    </button>
                  ))}
                </div>
              )}
            </section>
          )}
        </div>
      </main>
    </div>
  );
}