"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearSession, getSession } from "@/lib/auth";

const NAV = [
  { href: "/", label: "Dashboard" },
  { href: "/ventas", label: "Registro rápido" },
  { href: "/pedidos", label: "Pedidos" },
  { href: "/productos", label: "Productos" },
  { href: "/clientes", label: "Clientes" },
];

export function Sidebar() {
  const router = useRouter();
  const [email, setEmail] = useState<string | null>(null);

  useEffect(() => {
    const session = getSession();
    setEmail(session?.seller.email ?? null);
  }, []);

  function logout() {
    clearSession();
    router.push("/login");
    router.refresh();
  }

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-slate-800 bg-slate-900 p-4">
      <h2 className="mb-6 text-lg font-semibold text-emerald-400">Shopify Manager</h2>
      <ul className="flex-1 space-y-1 text-sm">
        {NAV.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className="block rounded-md px-3 py-2 text-slate-300 transition hover:bg-slate-800 hover:text-white"
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
      <div className="border-t border-slate-800 pt-3">
        {email ? (
          <>
            <p className="mb-2 truncate px-1 text-xs text-slate-400">{email}</p>
            <button
              onClick={logout}
              className="w-full rounded-md bg-slate-800 px-3 py-1.5 text-sm text-slate-300 transition hover:bg-slate-700"
            >
              Cerrar sesión
            </button>
          </>
        ) : (
          <Link
            href="/login"
            className="block rounded-md bg-emerald-600 px-3 py-1.5 text-center text-sm font-medium text-white transition hover:bg-emerald-500"
          >
            Iniciar sesión
          </Link>
        )}
      </div>
    </aside>
  );
}