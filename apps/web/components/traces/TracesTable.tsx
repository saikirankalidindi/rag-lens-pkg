"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useState } from "react";
import Link from "next/link";
import {
  ChevronLeft,
  ChevronRight,
  Search,
  X,
} from "lucide-react";
import { useTraces } from "@/hooks/use-raglens";
import {
  formatCost,
  formatDate,
  formatDuration,
  formatRelativeTime,
  formatTokens,
} from "@/lib/utils";
import { StatusBadge } from "@/components/ui/status-badge";
import type { TraceStatus } from "@/lib/types";

interface TracesTableProps {
  projectId: string;
}

const STATUS_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "All statuses" },
  { value: "success", label: "Success" },
  { value: "warning", label: "Warning" },
  { value: "error", label: "Error" },
];

const ENV_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "All environments" },
  { value: "development", label: "Development" },
  { value: "staging", label: "Staging" },
  { value: "production", label: "Production" },
];

const PAGE_SIZE = 25;

export function TracesTable({ projectId }: TracesTableProps) {
  const searchParams = useSearchParams();

  const [search, setSearch] = useState(searchParams.get("search") ?? "");
  const [status, setStatus] = useState(searchParams.get("status") ?? "");
  const [environment, setEnvironment] = useState(
    searchParams.get("env") ?? ""
  );
  const [page, setPage] = useState(
    Math.max(1, parseInt(searchParams.get("page") ?? "1", 10) || 1)
  );

  const [after, setAfter] = useState("");
  const [before, setBefore] = useState("");
  const [sort, setSort] = useState("newest");
  const invalidRange = !!(after && before && after > before);
  const beforeExclusive = before ? new Date(new Date(before + "T00:00:00Z").getTime() + 86400000).toISOString() : undefined;

  // Committed filter values (only applied on explicit search submit or dropdown change)
  const [committedSearch, setCommittedSearch] = useState(search);

  const { data, isLoading, isPlaceholderData, error, refetch } = useTraces(projectId, {
    page,
    page_size: PAGE_SIZE,
    started_after: after && !invalidRange ? after + "T00:00:00Z" : undefined,
    started_before: !invalidRange ? beforeExclusive : undefined,
    sort,
    status: status || undefined,
    search: committedSearch || undefined,
    environment: environment || undefined,
  });

  const traces = data?.items ?? [];
  const total = data?.total ?? 0;
  const hasNext = data?.has_next ?? false;
  const totalPages = Math.ceil(total / PAGE_SIZE);

  const handleSearch = useCallback(() => {
    setCommittedSearch(search);
    setPage(1);
  }, [search]);

  const handleStatusChange = (val: string) => {
    setStatus(val);
    setPage(1);
  };

  const handleEnvChange = (val: string) => {
    setEnvironment(val);
    setPage(1);
  };

  const clearFilters = () => {
    setAfter("");
    setBefore("");
    setSearch("");
    setCommittedSearch("");
    setStatus("");
    setEnvironment("");
    setPage(1);
  };

  const hasActiveFilters = committedSearch || status || environment || after || before;

  return (
    <div className="space-y-4">
      {/* Filter bar */}
      <div className="flex flex-wrap items-center gap-2">
        {/* Search input */}
        <div className="relative flex-1 min-w-48">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground pointer-events-none" />
          <input
            type="text"
            placeholder="Search traces…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            className="w-full rounded-md border border-border bg-card pl-8 pr-3 py-1.5 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>

        {/* Status filter */}
        <select
          aria-label="Status filter"
          value={status}
          onChange={(e) => handleStatusChange(e.target.value)}
          className="rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        {/* Environment filter */}
        <select
          aria-label="Environment filter"
          value={environment}
          onChange={(e) => handleEnvChange(e.target.value)}
          className="rounded-md border border-border bg-card px-2.5 py-1.5 text-sm text-foreground focus:outline-none focus:ring-1 focus:ring-ring"
        >
          {ENV_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>

        <button className="rounded border border-border px-3 py-1.5 text-sm" onClick={handleSearch}>Search</button>
        <label className="text-xs">From (UTC)<input aria-label="From date" type="date" value={after} onChange={(e) => { setAfter(e.target.value); setPage(1); }} className="ml-2 rounded border border-border bg-card px-2 py-1.5" /></label>
        <label className="text-xs">Through (UTC)<input aria-label="Through date" type="date" min={after || undefined} value={before} onChange={(e) => { setBefore(e.target.value); setPage(1); }} className="ml-2 rounded border border-border bg-card px-2 py-1.5" /></label>
        <select aria-label="Sort traces" value={sort} onChange={(e) => { setSort(e.target.value); setPage(1); }} className="rounded border border-border bg-card p-1.5 text-sm"><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="slowest">Slowest first</option><option value="fastest">Fastest first</option></select>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-1 rounded-md px-2 py-1.5 text-xs text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
          >
            <X className="h-3 w-3" />
            Clear
          </button>
        )}

        <div className="ml-auto text-xs text-muted-foreground">
          {total.toLocaleString()} trace{total !== 1 ? "s" : ""}
        </div>
      </div>

      {invalidRange && <p role="alert" className="text-destructive">The end date must be on or after the start date.</p>}
      {error && <p role="alert" className="text-destructive">{error.message} <button onClick={() => refetch()}>Retry</button></p>}
      {/* Table */}
      <div
        className={`rounded-lg border border-border bg-card overflow-x-auto transition-opacity ${
          isLoading || isPlaceholderData ? "opacity-70" : "opacity-100"
        }`}
      >
        {/* Table header */}
        <div className="min-w-[820px] grid grid-cols-[80px_1fr_90px_100px_70px_70px_100px_24px] gap-2 px-4 py-2 border-b border-border bg-muted/30">
          {["Status", "Query", "Duration", "Environment", "Tokens", "Cost", "Time"].map(
            (h, i) => (
              <span
                key={h}
                className={`text-[11px] font-medium text-muted-foreground uppercase tracking-wide ${
                  ""
                }`}
              >
                {h}
              </span>
            )
          )}
          {/* extra col for chevron */}
          <span />
        </div>

        {/* Rows */}
        {isLoading && traces.length === 0 ? (
          <div className="divide-y divide-border">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-12 animate-pulse bg-muted/10" />
            ))}
          </div>
        ) : error ? null : traces.length === 0 ? (
          <EmptyState projectId={projectId} hasFilters={!!hasActiveFilters} />
        ) : (
          <div className="divide-y divide-border">
            {traces.map((trace) => {
              const query = trace.input?.query as string | undefined;
              const model =
                (trace.metadata as Record<string, unknown> | null)
                  ?.environment as string | undefined;
              const tokens = trace.metrics?.total_tokens as number | undefined;
              const cost = trace.metrics?.estimated_cost as
                | number
                | undefined;

              return (
                <Link
                  key={trace.id}
                  href={`/projects/${projectId}/traces/${trace.id}`}
                  className="min-w-[820px] grid grid-cols-[80px_1fr_90px_100px_70px_70px_100px_24px] gap-2 items-center px-4 py-3 hover:bg-accent/30 transition-colors group"
                >
                  <div>
                    <StatusBadge status={trace.status as TraceStatus} />
                  </div>
                  <span className="text-sm text-foreground truncate">
                    {query ?? trace.name}
                  </span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {formatDuration(trace.duration_ms)}
                  </span>
                  <span className="text-xs text-muted-foreground truncate">
                    {model ?? "—"}
                  </span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {tokens != null ? formatTokens(tokens) : "—"}
                  </span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {cost != null ? formatCost(cost) : "—"}
                  </span>
                  <span className="text-xs text-muted-foreground tabular-nums">
                    {formatRelativeTime(trace.started_at)}
                  </span>
                  <ChevronRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity justify-self-end" />
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            Page {page} of {totalPages}
          </span>
          <div className="flex items-center gap-1">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="flex items-center gap-1 rounded px-2 py-1 hover:bg-accent/50 disabled:opacity-40 disabled:pointer-events-none transition-colors"
            >
              <ChevronLeft className="h-3.5 w-3.5" />
              Prev
            </button>
            <button
              disabled={!hasNext}
              onClick={() => setPage((p) => p + 1)}
              className="flex items-center gap-1 rounded px-2 py-1 hover:bg-accent/50 disabled:opacity-40 disabled:pointer-events-none transition-colors"
            >
              Next
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Empty state ────────────────────────────────────────────────────────────────

function EmptyState({
  projectId,
  hasFilters,
}: {
  projectId: string;
  hasFilters: boolean;
}) {
  if (hasFilters) {
    return (
      <div className="px-4 py-12 text-center">
        <p className="text-sm text-muted-foreground">
          No traces match your filters.
        </p>
      </div>
    );
  }

  return (
    <div className="px-6 py-12">
      <div className="max-w-lg mx-auto space-y-6">
        <div className="text-center">
          <h3 className="text-base font-semibold text-foreground">
            Send your first RAG trace
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            Instrument your pipeline once and every request will appear here.
          </p>
        </div>

        <div className="space-y-4 text-sm">
          <Step n={1} title="Install the SDK">
            <CodeBlock>pip install -e packages/sdk-python</CodeBlock>
          </Step>

          <Step n={2} title="Configure">
            <CodeBlock>{`from raglens import RAGLens\n\nraglens = RAGLens(api_key="rgl_test_...")`}</CodeBlock>
          </Step>

          <Step n={3} title="Instrument your pipeline">
            <CodeBlock>{`with raglens.trace(name="answer_question", input={"query": question}) as trace:\n    with trace.span(type="retrieval", name="vector_search") as span:\n        docs = retriever.invoke(question)\n        span.set_output({"results": [...]})\n\n    with trace.span(type="llm", name="generate") as span:\n        answer = llm.invoke(prompt)\n        span.set_output({"answer": answer})`}</CodeBlock>
          </Step>

          <Step n={4} title="Run your application">
            <p className="text-muted-foreground">
              Refresh this page after sending your first request.
            </p>
          </Step>
        </div>
      </div>
    </div>
  );
}

function Step({
  n,
  title,
  children,
}: {
  n: number;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex gap-3">
      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-[11px] font-bold text-primary">
        {n}
      </div>
      <div className="space-y-1.5 flex-1 min-w-0">
        <p className="font-medium text-foreground">{title}</p>
        {children}
      </div>
    </div>
  );
}

function CodeBlock({ children }: { children: string }) {
  return (
    <pre className="rounded-md bg-muted/50 border border-border px-3 py-2 text-xs font-mono text-foreground overflow-x-auto whitespace-pre">
      {children}
    </pre>
  );
}
