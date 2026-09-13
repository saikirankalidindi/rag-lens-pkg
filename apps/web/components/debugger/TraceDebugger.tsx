"use client";

import { useState } from "react";
import {
  AlertCircle,
  AlertTriangle,
  Clock,
  Cpu,
  DollarSign,
  Info,
} from "lucide-react";
import { useTrace } from "@/hooks/use-raglens";
import {
  formatCost,
  formatDate,
  formatDuration,
  formatTokens,
} from "@/lib/utils";
import { StatusBadge } from "@/components/ui/status-badge";
import type { Diagnostic, RetrievalResult, Span, TraceStatus } from "@/lib/types";
import {
  RetrievalInspector,
  RerankingInspector,
  ContextInspector,
  PromptInspector,
  LLMInspector,
} from "./inspectors";

interface TraceDebuggerProps {
  projectId: string;
  traceId: string;
}

// ── Span type config ─────────────────────────────────────────────────────────

const SPAN_TYPE_LABELS: Record<string, string> = {
  query: "Query",
  query_rewrite: "Query Rewrite",
  retrieval: "Retrieval",
  reranking: "Reranking",
  context: "Context",
  prompt: "Prompt",
  llm: "LLM",
  response: "Response",
  custom: "Custom",
};

const SPAN_COLORS: Record<string, string> = {
  query: "bg-sky-500",
  query_rewrite: "bg-indigo-500",
  retrieval: "bg-violet-500",
  reranking: "bg-purple-500",
  context: "bg-fuchsia-500",
  prompt: "bg-pink-500",
  llm: "bg-amber-500",
  response: "bg-emerald-500",
  custom: "bg-slate-500",
};

function spanColor(type: string) {
  return SPAN_COLORS[type] ?? "bg-slate-500";
}

// ── Diagnostic icons ──────────────────────────────────────────────────────────

function DiagnosticIcon({ severity }: { severity: string }) {
  if (severity === "error")
    return <AlertCircle className="h-4 w-4 text-red-400 shrink-0" />;
  if (severity === "warning")
    return <AlertTriangle className="h-4 w-4 text-amber-400 shrink-0" />;
  return <Info className="h-4 w-4 text-blue-400 shrink-0" />;
}

// ── Main component ────────────────────────────────────────────────────────────

function timelineRows(spans: Span[]) {
  const rows: Array<{ span: Span; depth: number }> = [];
  const visited = new Set<string>();
  const ids = new Set(spans.map(s => s.id));
  function visit(span: Span, depth: number) {
    if (visited.has(span.id)) return;
    visited.add(span.id);
    rows.push({ span, depth });
    for (const child of spans.filter(s => s.parent_span_id === span.id)) visit(child, depth + 1);
  }
  for (const span of spans.filter(s => !s.parent_span_id || !ids.has(s.parent_span_id))) visit(span, 0);
  for (const span of spans) visit(span, 0);
  return rows;
}

export function TraceDebugger({ projectId, traceId }: TraceDebuggerProps) {
  const { data: trace, isLoading, error, refetch } = useTrace(projectId, traceId);
  const [selectedSpanId, setSelectedSpanId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex flex-col h-full">
        <div className="border-b border-border p-5 space-y-3 animate-pulse">
          <div className="h-5 bg-muted/50 rounded w-2/3" />
          <div className="h-4 bg-muted/50 rounded w-1/3" />
        </div>
        <div className="flex flex-1 min-h-0">
          <div className="w-80 border-r border-border animate-pulse bg-muted/10" />
          <div className="flex-1 animate-pulse bg-muted/5" />
        </div>
      </div>
    );
  }

  if (error || !trace) {
    return (
      <div className="flex items-center justify-center h-full">
        <p role="alert" className="text-sm text-muted-foreground">{error?.message ?? "Trace not found."} <button onClick={() => refetch()}>Retry</button></p>
      </div>
    );
  }

  const query = trace.input?.query as string | undefined;
  const tokens = trace.metrics?.total_tokens as number | undefined;
  const cost = trace.metrics?.estimated_cost as number | undefined;

  const selectedSpan = trace.spans.find((s) => s.id === selectedSpanId) ?? null;
  const autoSelected = selectedSpan ?? trace.spans[0] ?? null;

  const totalDurationMs = trace.duration_ms || 1;

  // Diagnostics summary counts
  const warnings = trace.diagnostics.filter(
    (d) => d.severity === "warning" || d.severity === "error"
  ).length;
  const infos = trace.diagnostics.filter((d) => d.severity === "info").length;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="border-b border-border px-5 py-4 shrink-0">
        <div className="flex items-start gap-4">
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-semibold text-foreground leading-tight truncate">
              {query ?? trace.name}
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5 font-mono">
              {trace.id}
            </p>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <StatusBadge status={trace.status as TraceStatus} />
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Clock className="h-3 w-3" />
              {formatDuration(trace.duration_ms)}
            </span>
            {tokens != null && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <Cpu className="h-3 w-3" />
                {formatTokens(tokens)}
              </span>
            )}
            {cost != null && (
              <span className="text-xs text-muted-foreground flex items-center gap-1">
                <DollarSign className="h-3 w-3" />
                {formatCost(cost)}
              </span>
            )}
          </div>
        </div>

        {/* Diagnostics banner */}
        {trace.diagnostics.length > 0 && (
          <div className="mt-3 flex items-center gap-3">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Diagnostics
            </span>
            {warnings > 0 && (
              <span className="inline-flex items-center gap-1 text-xs text-amber-400">
                <AlertTriangle className="h-3 w-3" />
                {warnings} warning{warnings !== 1 ? "s" : ""}
              </span>
            )}
            {infos > 0 && (
              <span className="inline-flex items-center gap-1 text-xs text-blue-400">
                <Info className="h-3 w-3" />
                {infos} insight{infos !== 1 ? "s" : ""}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Body: timeline + inspector */}
      <div className="flex flex-col lg:flex-row flex-1 min-h-0 overflow-hidden">
        {/* Left panel — span timeline */}
        <div className="w-full lg:w-72 max-h-48 lg:max-h-none shrink-0 border-b lg:border-r border-border overflow-y-auto">
          <div className="px-3 pt-3 pb-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
              Trace
            </p>
          </div>
          <div className="px-2 pb-3 space-y-0.5">
            {timelineRows(trace.spans).map(({ span, depth }) => {
              const isSelected =
                (selectedSpanId ?? autoSelected?.id) === span.id;
              const leftPct =
                trace.started_at
                  ? Math.max(
                      0,
                      ((new Date(span.started_at).getTime() -
                        new Date(trace.started_at).getTime()) /
                        totalDurationMs) *
                        100
                    )
                  : 0;
              const widthPct = Math.max(
                1,
                (span.duration_ms / totalDurationMs) * 100
              );

              return (
                <button
                  key={span.id}
                  aria-label={`Inspect ${span.name}`}
                  aria-pressed={isSelected}
                  style={{ paddingLeft: `${8 + Math.min(depth, 6) * 12}px` }}
                  onClick={() =>
                    setSelectedSpanId(isSelected ? null : span.id)
                  }
                  className={`w-full text-left rounded px-2 py-1.5 transition-colors group ${
                    isSelected
                      ? "bg-accent text-accent-foreground"
                      : "hover:bg-accent/50"
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`h-2 w-2 rounded-full shrink-0 ${spanColor(span.type)}`}
                    />
                    <span className="flex-1 text-xs text-foreground truncate">
                      {span.name}
                    </span>
                    <span className="text-[11px] text-muted-foreground tabular-nums shrink-0">
                      {formatDuration(span.duration_ms)}
                    </span>
                    {span.status === "error" && (
                      <AlertCircle className="h-3 w-3 text-red-400 shrink-0" />
                    )}
                  </div>
                  {/* Duration bar */}
                  <div className="mt-1 ml-4 h-1 bg-muted/30 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full ${spanColor(span.type)} opacity-60`}
                      style={{
                        marginLeft: `${leftPct}%`,
                        width: `${Math.min(widthPct, 100 - leftPct)}%`,
                      }}
                    />
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Right panel — inspector */}
        <div className="min-w-0 flex-1 overflow-y-auto">
          <SpanInspector
            span={selectedSpanId ? selectedSpan : autoSelected}
            trace={trace}
          />
        </div>
      </div>

      {/* Diagnostics panel — below when present */}
      {trace.diagnostics.length > 0 && (
        <DiagnosticsPanel
          diagnostics={trace.diagnostics}
          onSpanClick={(spanId) => setSelectedSpanId(spanId)}
        />
      )}
    </div>
  );
}

// ── Inspector panel ───────────────────────────────────────────────────────────

function SpanInspector({
  span,
  trace,
}: {
  span: Span | null;
  trace: ReturnType<typeof useTrace>["data"];
}) {
  if (!span) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-sm text-muted-foreground">
          Select a span to inspect.
        </p>
      </div>
    );
  }

  // Pull retrieval results for this span
  const previousRetrieval = span.type === "reranking" ? trace?.spans
    .filter(s => s.type === "retrieval" && s.parent_span_id === span.parent_span_id &&
      new Date(s.started_at).getTime() <= new Date(span.started_at).getTime() &&
      s.retrieval_results?.some(r => r.reranked_rank != null))
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())[0] : undefined;
  const retrievalResults: RetrievalResult[] = span.retrieval_results?.length
    ? span.retrieval_results : previousRetrieval?.retrieval_results ?? [];

  return (
    <div className="p-5 space-y-5">
      {/* Span header */}
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <div
            className={`h-2.5 w-2.5 rounded-full ${spanColor(span.type)}`}
          />
          <h3 className="text-sm font-semibold text-foreground">{span.name}</h3>
          <StatusBadge status={span.status as TraceStatus} />
        </div>
        <p className="text-xs text-muted-foreground font-mono">{span.id}</p>
        <div className="flex items-center gap-4 text-xs text-muted-foreground">
          <span>
            <Clock className="inline h-3 w-3 mr-1" />
            {formatDuration(span.duration_ms)}
          </span>
          <span>{formatDate(span.started_at)}</span>
        </div>
      </div>

      {/* Type-specific inspectors */}
      {span.type === "retrieval" && (
        <Section title="Retrieval Results">
          <RetrievalInspector results={retrievalResults} />
        </Section>
      )}

      {span.type === "reranking" && (
        <Section title="Reranking Analysis">
          <RerankingInspector results={retrievalResults} />
        </Section>
      )}

      {span.type === "context" && (
        <Section title="Context Assembly">
          <ContextInspector span={span} />
        </Section>
      )}

      {span.type === "prompt" && (
        <Section title="Prompt Details">
          <PromptInspector span={span} />
        </Section>
      )}

      {span.type === "llm" && (
        <Section title="LLM Execution">
          <LLMInspector span={span} metrics={trace?.metrics} />
        </Section>
      )}

      {/* Fallback: show attributes, input, output for other types */}
      {!["retrieval", "reranking", "context", "prompt", "llm"].includes(span.type) && (
        <>
          {/* Attributes */}
          {span.attributes && Object.keys(span.attributes).length > 0 && (
            <Section title="Attributes">
              <AttributeTable data={span.attributes} />
            </Section>
          )}

          {/* Input */}
          {span.input && Object.keys(span.input).length > 0 && (
            <Section title="Input">
              <JsonView data={span.input} />
            </Section>
          )}

          {/* Output */}
          {span.output && Object.keys(span.output).length > 0 && (
            <Section title="Output">
              <JsonView data={span.output} />
            </Section>
          )}
        </>
      )}
    </div>
  );
}

// ── Diagnostics panel ─────────────────────────────────────────────────────────

function DiagnosticsPanel({
  diagnostics,
  onSpanClick,
}: {
  diagnostics: Diagnostic[];
  onSpanClick?: (spanId: string) => void;
}) {
  return (
    <div className="border-t border-border bg-muted/10 px-5 py-4 shrink-0 max-h-56 overflow-y-auto">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-3">
        Diagnostics
      </p>
      <div className="space-y-3">
        {diagnostics.map((d) => (
          <div
            key={d.id}
            role={d.span_id ? "button" : undefined}
            tabIndex={d.span_id ? 0 : undefined}
            onKeyDown={(e) => { if (d.span_id && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); onSpanClick?.(d.span_id); } }}
            className={`rounded-md border px-3 py-2.5 text-xs space-y-1 transition-all ${
              d.severity === "error"
                ? "border-red-500/30 bg-red-500/5"
                : d.severity === "warning"
                ? "border-amber-500/30 bg-amber-500/5"
                : "border-blue-500/30 bg-blue-500/5"
            } ${d.span_id && onSpanClick ? "cursor-pointer hover:border-opacity-60" : ""}`}
            onClick={() => d.span_id && onSpanClick?.(d.span_id)}
          >
            <div className="flex items-center gap-2">
              <DiagnosticIcon severity={d.severity} />
              <span className="font-semibold text-foreground uppercase text-[11px] tracking-wide">
                {d.title}
              </span>
              <span className="ml-auto text-[10px] text-muted-foreground capitalize">
                {d.category}
              </span>
              {d.span_id && onSpanClick && (
                <span className="text-[10px] text-primary">
                  Click to view span →
                </span>
              )}
            </div>
            <p className="text-muted-foreground leading-relaxed">
              {d.description}
            </p>
            {/* Evidence display */}
            {d.evidence && Object.keys(d.evidence).length > 0 && (
              <div className="pt-1 space-y-0.5">
                {Object.entries(d.evidence).map(([key, value]) => (
                  <div key={key} className="flex gap-2 text-[11px]">
                    <span className="text-foreground/60 capitalize">
                      {key.replace(/_/g, " ")}:
                    </span>
                    <span className="text-foreground font-medium font-mono">
                      {typeof value === "number" ? value.toFixed(4) : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            )}
            {d.suggestions.length > 0 && (
              <ul className="space-y-0.5 pt-1">
                {d.suggestions.map((s, i) => (
                  <li key={i} className="flex gap-1.5 text-muted-foreground">
                    <span className="text-foreground/40 shrink-0">•</span>
                    {s}
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Shared UI helpers ─────────────────────────────────────────────────────────

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </p>
      {children}
    </div>
  );
}

function AttributeTable({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="rounded-md border border-border overflow-hidden text-xs">
      {Object.entries(data).map(([k, v], i) => (
        <div
          key={k}
          className={`flex gap-4 px-3 py-1.5 ${
            i % 2 === 0 ? "bg-muted/10" : ""
          }`}
        >
          <span className="text-muted-foreground w-32 shrink-0">{k}</span>
          <span className="text-foreground break-all">{String(v)}</span>
        </div>
      ))}
    </div>
  );
}

function JsonView({ data }: { data: Record<string, unknown> }) {
  return (
    <pre className="rounded-md border border-border bg-muted/10 px-3 py-2 text-xs font-mono text-foreground overflow-x-auto whitespace-pre-wrap break-words">
      {JSON.stringify(data, null, 2)}
    </pre>
  );
}
