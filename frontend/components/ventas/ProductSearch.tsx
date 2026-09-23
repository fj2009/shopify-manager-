"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";

export type VariantHit = {
  variant_shopify_id: string;
  product_title: string;
  variant_title: string;
  sku: string | null;
  stock: number;
  price: string;
  image_url: string | null;
};

export function ProductSearch({ onSelect }: { onSelect: (hit: VariantHit) => void }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<VariantHit[]>([]);
  const [open, setOpen] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (timer.current) clearTimeout(timer.current);
    if (!query.trim()) {
      setResults([]);
      return;
    }
    timer.current = setTimeout(async () => {
      try {
        const hits = await api<VariantHit[]>(
          `/products/search?q=${encodeURIComponent(query)}`
        );
        setResults(hits);
        setOpen(true);
      } catch {
        setResults([]);
      }
    }, 250);
  }, [query]);

  function pick(hit: VariantHit) {
    onSelect(hit);
    setQuery("");
    setResults([]);
    setOpen(false);
  }

  return (
    <div className="relative">
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => results.length > 0 && setOpen(true)}
        placeholder="Buscar lámpara (nombre, variante o SKU)…"
        className="w-full rounded-xl border border-slate-700 bg-slate-900 px-4 py-3 text-lg placeholder-slate-500 focus:border-emerald-500 focus:outline-none"
      />
      {open && results.length > 0 && (
        <ul className="absolute z-10 mt-2 max-h-80 w-full overflow-auto rounded-xl border border-slate-800 bg-slate-900 shadow-2xl">
          {results.map((hit) => (
            <li key={hit.variant_shopify_id}>
              <button
                type="button"
                onClick={() => pick(hit)}
                className="flex w-full items-center gap-3 px-3 py-2 text-left transition hover:bg-slate-800"
              >
                {hit.image_url ? (
                  // eslint-disable-next-line @next/next/no-img-element
                  <img src={hit.image_url} alt="" className="h-10 w-10 rounded object-cover" />
                ) : (
                  <div className="h-10 w-10 rounded bg-slate-800" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-white">{hit.product_title}</p>
                  <p className="truncate text-xs text-slate-400">
                    {hit.variant_title} · {hit.sku ?? "sin SKU"} · ${hit.price}
                  </p>
                </div>
                <span
                  className={`text-xs ${hit.stock <= 5 ? "text-amber-400" : "text-slate-400"}`}
                >
                  {hit.stock} uds
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}