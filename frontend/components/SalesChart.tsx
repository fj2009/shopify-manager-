"use client";

import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export function SalesChart({ data }: { data: { label: string; ventas: number }[] }) {
  return (
    <div className="h-72 rounded-xl border border-slate-800 bg-slate-900 p-4">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data}>
          <defs>
            <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
          <XAxis dataKey="label" stroke="#94a3b8" fontSize={12} />
          <YAxis stroke="#94a3b8" fontSize={12} allowDecimals={false} />
          <Tooltip contentStyle={{ background: "#0f172a", border: "1px solid #1e293b" }} />
          <Area type="monotone" dataKey="ventas" stroke="#10b981" fill="url(#fill)" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}