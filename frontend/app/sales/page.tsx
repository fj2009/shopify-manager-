"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ClientField } from "@/components/ventas/ClientField";
import { ProductSearch, type VariantHit } from "@/components/ventas/ProductSearch";
import { Sidebar } from "@/components/Sidebar";
import { api } from "@/lib/api";
import { clearSession, getSession } from "@/lib/auth";

export default function FastEntryPage() {
  const router = useRouter();
  const [variant, setVariant] = useState<VariantHit | null>(null);
  const [clientEmail, setClientEmail] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getSession()) router.replace("/login");
  }, [router]);

  const total = variant ? (parseFloat(variant.price) * quantity).toFixed(2) : "0.00";

  async function sell() {
    if (!variant || !clientEmail) return;
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      await api("/sales", {
        method: "POST",
        body: JSON.stringify({
          client_email: clientEmail,
          product_variant_shopify_id: variant.variant_shopify_id,
          quantity,
          unit_price: variant.price,
          workshop_note: note || null,
        }),
      });
      setMessage(`Venta registrada: ${quantity} × ${variant.product_title}`);
      setVariant(null);
      setClientEmail("");
      setQuantity(1);
      setNote("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al registrar la venta");
      if (e instanceof Error && e.message.includes("401")) clearSession();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex">
      <Sidebar />
      <main className="mx-auto w-full max-w-2xl flex-1 space-y-5 p-6">
        <header>
          <h1 className="text-2xl font-bold">Registro rápido</h1>
          <p className="text-sm text-slate-400">Venta registrada en segundos, sin formularios largos.</p>
        </header>

        <ProductSearch onSelect={setVariant} />

        {variant && (
          <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate font-semibold text-white">{variant.product_title}</p>
                <p className="truncate text-sm text-slate-400">
                  {variant.variant_title} · {variant.sku ?? "sin SKU"}
                </p>
              </div>
              <span
                className={`shrink-0 text-xs ${
                  variant.stock <= 5 ? "text-amber-400" : "text-slate-400"
                }`}
              >
                stock: {variant.stock}
              </span>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <label className="block">
                <span className="text-xs text-slate-400">Cantidad</span>
                <input
                  type="number"
                  min={1}
                  value={quantity}
                  onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                  className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-white focus:border-emerald-500 focus:outline-none"
                />
              </label>
              <div>
                <span className="text-xs text-slate-400">Total</span>
                <p className="mt-1 text-lg font-bold text-emerald-400">${total}</p>
              </div>
            </div>
          </div>
        )}

        <ClientField value={clientEmail} onChange={setClientEmail} />

        <label className="block">
          <span className="text-xs text-slate-400">Nota de taller (opcional)</span>
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            placeholder="Ej: cable negro 2 m, sin regulador…"
            className="mt-1 w-full resize-none rounded-xl border border-slate-700 bg-slate-900 px-3 py-2 text-white placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
          />
        </label>

        {error && <p className="text-sm text-rose-400">{error}</p>}
        {message && <p className="text-sm text-emerald-400">{message}</p>}

        <button
          onClick={sell}
          disabled={busy || !variant || !clientEmail || quantity < 1}
          className="w-full rounded-xl bg-emerald-600 py-3 text-lg font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {busy ? "Registrando…" : "Vender"}
        </button>
      </main>
    </div>
  );
}