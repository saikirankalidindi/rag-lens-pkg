"use client";

import { Activity, Clock, Cpu, Zap } from "lucide-react";
import Link from "next/link";
import { useProjectStats, useTraces } from "@/hooks/use-raglens";
import { formatDuration, formatTokens, formatRelativeTime, formatCost } from "@/lib/utils";
import { StatusBadge } from "@/components/ui/status-badge";
import type { TraceStatus } from "@/lib/types";

interface OverviewStatsProps {
  projectId: string;
}

function MetricCard({
  label,
  value,
  icon: Icon,
  sub,
}: {
  label: string;
  value: string;
  icon: React.ElementType;
  sub?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
          {label}
        </span>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="text-2xl font-semibold text-foreground tabular-nums">
        {value}
      </div>
      {sub && (
        <div className="text-xs text-muted-foreground">{sub}</div>
      )}
    </div>
  );
}

export function OverviewStats({ projectId }: OverviewStatsProps) {
  const { data: stats, isLoading, error, refetch } = useProjectStats(projectId);

  if (isLoading) {
    return (
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div
            key={i}
            className="h-24 rounded-lg border border-border bg-card animate-pulse"
          />
        ))}
      </div>
    );
  }

  if (error) return <p role="alert">{error.message} <button onClick={() => refetch()}>Retry</button></p>;
  if (!stats) return null;

  const errorPct = (stats.error_rate * 100).toFixed(1);
  const avgLatency = stats.avg_latency_ms < 1000
    ? `${Math.round(stats.avg_latency_ms)}ms`
    : `${(stats.avg_latency_ms / 1000).toFixed(2)}s`;

  return (
    <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <MetricCard
        label="Total traces"
        value={stats.total_traces.toLocaleString()}
        icon={Activity}
      />
      <MetricCard
        label="Success rate"
        value={stats.total_traces ? `${(stats.success_rate * 100).toFixed(1)}%` : "—"}
        icon={Zap}
      />
      <MetricCard
        label="Avg Latency"
        value={avgLatency}
        icon={Clock}
      />
      <MetricCard
        label="Total tokens"
        value={formatTokens(stats.total_tokens)}
        icon={Cpu}
      />
    </div>
  );
}

export function RecentTraces({ projectId }: OverviewStatsProps) {
  const { data, isLoading, error, refetch } = useTraces(projectId, { page: 1, page_size: 10 });

  if (isLoading) {
    return (
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="px-4 py-3 border-b border-border">
          <h3 className="text-sm font-medium text-foreground">Recent Traces</h3>
        </div>
        <div className="divide-y divide-border">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-12 animate-pulse bg-muted/20" />
          ))}
        </div>
      </div>
    );
  }

  if (error) return <p role="alert">{error.message} <button onClick={() => refetch()}>Retry</button></p>;
  const traces = data?.items ?? [];

  if (traces.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 text-center">
        <p className="text-sm text-muted-foreground">No traces yet.</p>
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      <div className="px-4 py-3 border-b border-border flex items-center justify-between">
        <h3 className="text-sm font-medium text-foreground">Recent Traces</h3>
        <Link
          href={`/projects/${projectId}/traces`}
          className="text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          View all →
        </Link>
      </div>
      <div className="divide-y divide-border">
        {traces.map((trace) => {
          const query = trace.input?.query as string | undefined;
          const tokens = trace.metrics?.total_tokens as number | undefined;
          const cost = trace.metrics?.estimated_cost as number | undefined;
          return (
            <Link
              key={trace.id}
              href={`/projects/${projectId}/traces/${trace.id}`}
              className="flex items-center gap-4 px-4 py-3 hover:bg-accent/40 transition-colors group"
            >
              <StatusBadge status={trace.status as TraceStatus} />
              <span className="flex-1 min-w-0 text-sm text-foreground truncate">
                {query ?? trace.name}
              </span>
              <span className="text-xs text-muted-foreground tabular-nums shrink-0">
                {formatDuration(trace.duration_ms)}
              </span>
              {tokens != null && (
                <span className="text-xs text-muted-foreground tabular-nums shrink-0 hidden lg:block">
                  {formatTokens(tokens)}
                </span>
              )}
              {cost != null && (
                <span className="text-xs text-muted-foreground tabular-nums shrink-0 hidden xl:block">
                  {formatCost(cost)}
                </span>
              )}
              <span className="text-xs text-muted-foreground tabular-nums shrink-0">
                {formatRelativeTime(trace.started_at)}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
