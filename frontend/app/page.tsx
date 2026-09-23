"use client";

import { useEffect, useState } from "react";
import { KpiCard } from "@/components/KpiCard";
import { SalesChart } from "@/components/SalesChart";
import { Sidebar } from "@/components/Sidebar";
import { api } from "@/lib/api";

type Overview = {
  sales_today: number;
  sales_month: number;
  revenue_today: string;
  revenue_month: string;
  sellers: { seller: string; units: number; progress: number }[];
  top_products: { title: string; units: number; revenue: string }[];
  critical_stock: { product_title: string; variant_title: string | null; stock: number }[];
  trend: { day: string; units: number; revenue: string }[];
};

const money = (value: string) =>
  Number(value).toLocaleString("es-MX", { minimumFractionDigits: 2 });

export default function DashboardPage() {
  const [data, setData] = useState<Overview | null>(null);

  useEffect(() => {
    api<Overview>("/dashboard/overview").then(setData).catch(console.error);
  }, []);

  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 space-y-6 p-6">
        <header className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold">Panel de Ventas</h1>
            <p className="text-sm text-slate-400">Pulse diario de la operación</p>
          </div>
          <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-sm text-emerald-400">
            Live
          </span>
        </header>

        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <KpiCard label="Ventas hoy" value={data?.sales_today ?? 0} />
          <KpiCard label="Ventas del mes" value={data?.sales_month ?? 0} />
          <KpiCard
            label="Ingresos hoy"
            value={data ? `$${money(data.revenue_today)}` : "—"}
          />
          <KpiCard
            label="Ingresos del mes"
            value={data ? `$${money(data.revenue_month)}` : "—"}
          />
        </div>

        <SalesChart
          data={(data?.trend ?? []).map((p) => ({
            label: new Date(p.day).toLocaleDateString("es", { day: "2-digit", month: "2-digit" }),
            ventas: p.units,
          }))}
        />

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-300">Metas del mes</h2>
            <ul className="space-y-3">
              {data?.sellers.length ? (
                data.sellers.map((s) => (
                  <li key={s.seller}>
                    <div className="flex justify-between text-sm">
                      <span className="text-white">{s.seller}</span>
                      <span className="text-slate-400">
                        {s.units} uds · {s.progress}%
                      </span>
                    </div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-slate-800">
                      <div
                        className="h-2 rounded-full bg-emerald-500 transition-all"
                        style={{ width: `${Math.min(s.progress, 100)}%` }}
                      />
                    </div>
                  </li>
                ))
              ) : (
                <p className="text-sm text-slate-500">Sin vendedores.</p>
              )}
            </ul>
          </section>

          <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
            <h2 className="mb-3 text-sm font-semibold text-slate-300">
              Top lámparas del mes
            </h2>
            <ul className="space-y-2">
              {data?.top_products.length ? (
                data.top_products.map((p, i) => (
                  <li key={p.title} className="flex items-center justify-between text-sm">
                    <span className="text-white">
                      <span className="mr-1 text-emerald-400">{i + 1}.</span> {p.title}
                    </span>
                    <span className="text-slate-400">
                      {p.units} uds · ${money(p.revenue)}
                    </span>
                  </li>
                ))
              ) : (
                <p className="text-sm text-slate-500">Sin ventas registradas este mes.</p>
              )}
            </ul>
          </section>
        </div>

        {data && data.critical_stock.length > 0 && (
          <section className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
            <h2 className="mb-2 text-sm font-semibold text-amber-300">Stock crítico</h2>
            <ul className="space-y-1 text-sm text-slate-200">
              {data.critical_stock.map((c, i) => (
                <li key={i}>
                  {c.product_title}
                  {c.variant_title ? ` · ${c.variant_title}` : ""} —{" "}
                  <span className="font-semibold text-amber-400">{c.stock} uds</span>
                </li>
              ))}
            </ul>
          </section>
        )}
      </main>
    </div>
  );
}