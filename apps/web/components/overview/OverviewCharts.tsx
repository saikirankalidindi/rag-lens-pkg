"use client";

import { useProjectStats } from "@/hooks/use-raglens";

function SeriesChart({ title, labels, values, area = false, bars = false }: {
  title: string; labels: string[]; values: number[]; area?: boolean; bars?: boolean;
}) {
  const max = Math.max(1, ...values);
  const x = (i: number) => 35 + i * 300 / Math.max(1, values.length - 1);
  const y = (v: number) => 145 - v / max * 115;
  const points = values.map((v, i) => `${x(i)},${y(v)}`).join(" ");
  return <section className="min-w-0 rounded-lg border border-border bg-card p-4">
    <h2 className="text-sm font-medium">{title}</h2>
    <svg viewBox="0 0 370 180" role="img" aria-label={title} className="w-full text-primary">
      <line x1="35" y1="145" x2="350" y2="145" stroke="currentColor" opacity=".3" />
      <text x="2" y="30" fontSize="10" fill="currentColor">{max.toLocaleString()}</text>
      <text x="18" y="148" fontSize="10" fill="currentColor">0</text>
      {bars ? values.map((v, i) => <g key={labels[i]}><rect x={42 + i * 62} y={y(v)} width="38" height={145-y(v)} fill="currentColor"><title>{labels[i]}: {v}</title></rect><text x={60+i*62} y="164" textAnchor="middle" fontSize="9" fill="currentColor">{labels[i]}</text></g>) : <>
        {area && <polygon points={`35,145 ${points} 335,145`} fill="currentColor" opacity=".15" />}
        <polyline points={points} fill="none" stroke="currentColor" strokeWidth="2" />
        {values.map((v, i) => <circle key={labels[i]} cx={x(i)} cy={y(v)} r="2" fill="currentColor"><title>{labels[i]}: {v.toLocaleString()}</title></circle>)}
        <text x="35" y="164" fontSize="10" fill="currentColor">{labels[0]}</text><text x="335" y="164" textAnchor="end" fontSize="10" fill="currentColor">{labels.at(-1)}</text>
      </>}
    </svg>
    <details className="text-xs text-muted-foreground"><summary className="cursor-pointer">View chart data</summary><table className="mt-2 w-full"><thead><tr><th className="text-left">Period</th><th className="text-right">Value</th></tr></thead><tbody>{labels.map((label, i) => <tr key={label}><td>{label}</td><td className="text-right">{values[i].toLocaleString()}</td></tr>)}</tbody></table></details>
  </section>;
}

export function OverviewCharts({ projectId }: { projectId: string }) {
  const { data } = useProjectStats(projectId);
  if (!data) return null;
  return <div className="grid gap-4 xl:grid-cols-3">
    <SeriesChart title="Requests over time · last 30 days (UTC)" labels={data.activity.map(p => p.date)} values={data.activity.map(p => p.requests)} />
    <SeriesChart title="Latency distribution · all traces" labels={data.latency_buckets.map(p => p.label)} values={data.latency_buckets.map(p => p.count)} bars />
    <SeriesChart title="Token usage · last 30 days (UTC)" labels={data.activity.map(p => p.date)} values={data.activity.map(p => p.tokens)} area />
  </div>;
}
