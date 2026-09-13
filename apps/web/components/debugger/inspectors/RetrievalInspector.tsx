"use client";

import { CheckCircle2, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import type { RetrievalResult } from "@/lib/types";

interface RetrievalInspectorProps {
  results: RetrievalResult[];
}

export function RetrievalInspector({ results }: RetrievalInspectorProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set());

  if (results.length === 0) {
    return (
      <div className="rounded-md border border-border bg-muted/10 px-4 py-8 text-center">
        <p className="text-sm text-muted-foreground">No retrieval results</p>
      </div>
    );
  }

  const selectedCount = results.filter((r) => r.selected).length;
  const avgScore = results.reduce((sum, r) => sum + r.score, 0) / results.length;
  const maxScore = Math.max(...results.map((r) => r.score));
  const minScore = Math.min(...results.map((r) => r.score));
  const hasReranking = results.some((r) => r.reranked_rank != null);

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedIds);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedIds(newExpanded);
  };

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Retrieved" value={results.length} />
        <StatCard label="Selected" value={selectedCount} />
        <StatCard label="Avg Score" value={avgScore.toFixed(3)} />
        <StatCard
          label="Score Range"
          value={`${minScore.toFixed(2)} - ${maxScore.toFixed(2)}`}
        />
      </div>

      {/* Results list */}
      <div className="space-y-2">
        {results.map((result, idx) => {
          const isExpanded = expandedIds.has(result.id);
          const scorePercent = (result.score / maxScore) * 100;
          const hasRankChange =
            hasReranking &&
            result.reranked_rank != null &&
            result.reranked_rank !== result.rank;

          return (
            <div
              key={result.id}
              className={`rounded-lg border transition-all ${
                result.selected
                  ? "border-violet-500/40 bg-violet-500/5 shadow-sm"
                  : "border-border bg-card hover:border-border/60"
              }`}
            >
              {/* Header - always visible */}
              <button
                onClick={() => toggleExpanded(result.id)}
                className="w-full px-4 py-3 text-left flex items-start gap-3 group"
              >
                {/* Expand icon */}
                <div className="shrink-0 mt-0.5">
                  {isExpanded ? (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                  ) : (
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  )}
                </div>

                {/* Rank badge */}
                <div
                  className={`shrink-0 h-6 w-6 rounded-full flex items-center justify-center text-xs font-semibold ${
                    result.selected
                      ? "bg-violet-500 text-white"
                      : "bg-muted text-muted-foreground"
                  }`}
                >
                  {result.rank}
                </div>

                {/* Main content */}
                <div className="flex-1 min-w-0 space-y-1.5">
                  {/* Document name + selected badge */}
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground truncate">
                      {result.document_name}
                    </span>
                    {result.selected && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 text-xs font-medium shrink-0">
                        <CheckCircle2 className="h-3 w-3" />
                        Selected
                      </span>
                    )}
                  </div>

                  {/* Preview (collapsed state) */}
                  {!isExpanded && (
                    <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                      {result.content}
                    </p>
                  )}

                  {/* Score bar and metadata row */}
                  <div className="flex items-center gap-3">
                    {/* Score visualization */}
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-muted-foreground">
                          {result.retrieval_method}
                        </span>
                        <span className="font-mono text-foreground tabular-nums">
                          {result.score.toFixed(4)}
                        </span>
                      </div>
                      <div className="h-1.5 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all ${
                            result.selected ? "bg-violet-500" : "bg-primary/60"
                          }`}
                          style={{ width: `${scorePercent}%` }}
                        />
                      </div>
                    </div>

                    {/* Reranking indicator */}
                    {hasRankChange && (
                      <div className="shrink-0 px-2 py-1 rounded bg-purple-500/10 text-purple-400 text-xs font-medium">
                        #{result.reranked_rank} reranked
                      </div>
                    )}
                  </div>
                </div>
              </button>

              {/* Expanded content */}
              {isExpanded && (
                <div className="px-4 pb-4 space-y-3 border-t border-border/50">
                  {/* Full content */}
                  <div className="pt-3">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                      Content
                    </p>
                    <div className="rounded-md bg-muted/30 px-3 py-2.5">
                      <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                        {result.content}
                      </p>
                    </div>
                  </div>

                  {/* Reranking details */}
                  {hasReranking && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                        Reranking
                      </p>
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="rounded bg-muted/20 px-3 py-2">
                          <div className="text-muted-foreground">
                            Original Rank
                          </div>
                          <div className="font-semibold text-foreground mt-0.5">
                            #{result.rank}
                          </div>
                        </div>
                        <div className="rounded bg-muted/20 px-3 py-2">
                          <div className="text-muted-foreground">
                            Reranked Position
                          </div>
                          <div className="font-semibold text-foreground mt-0.5">
                            {result.reranked_rank != null
                              ? `#${result.reranked_rank}`
                              : "—"}
                          </div>
                        </div>
                        <div className="rounded bg-muted/20 px-3 py-2">
                          <div className="text-muted-foreground">
                            Reranker Score
                          </div>
                          <div className="font-semibold text-foreground mt-0.5 font-mono tabular-nums">
                            {result.reranker_score != null
                              ? result.reranker_score.toFixed(4)
                              : "—"}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Metadata */}
                  {result.metadata && Object.keys(result.metadata).length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
                        Metadata
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(result.metadata).map(([key, value]) => (
                          <div
                            key={key}
                            className="inline-flex items-center gap-1.5 px-2 py-1 rounded bg-muted/30 text-xs"
                          >
                            <span className="text-muted-foreground">{key}:</span>
                            <span className="text-foreground font-medium">
                              {String(value)}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* IDs (for debugging) */}
                  <div className="pt-2 flex gap-4 text-xs font-mono text-muted-foreground">
                    <span>Chunk: {result.chunk_id}</span>
                    <span>Doc: {result.document_id}</span>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <p className="text-base font-semibold text-foreground mt-1 tabular-nums">
        {value}
      </p>
    </div>
  );
}
