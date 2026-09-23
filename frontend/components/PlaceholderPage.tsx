"use client";

import { Sidebar } from "@/components/Sidebar";

export default function PlaceholderPage({ title, hint }: { title: string; hint: string }) {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex flex-1 flex-col items-center justify-center gap-2 p-6">
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-sm text-slate-400">{hint}</p>
      </main>
    </div>
  );
}