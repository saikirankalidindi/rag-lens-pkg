"use client";

import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import type { RetrievalResult } from "@/lib/types";

interface RerankingInspectorProps {
  results: RetrievalResult[];
}

interface RankChange {
  result: RetrievalResult;
  originalRank: number;
  newRank: number;
  delta: number;
  scoreDelta: number;
}

export function RerankingInspector({ results }: RerankingInspectorProps) {
  // Filter results that have reranking data
  const rerankedResults = results.filter((r) => r.reranked_rank != null);

  if (rerankedResults.length === 0) {
    return (
      <div className="rounded-md border border-border bg-muted/10 px-4 py-8 text-center">
        <p className="text-sm text-muted-foreground">
          No reranking data available
        </p>
      </div>
    );
  }

  // Calculate rank changes
  const changes: RankChange[] = rerankedResults.map((r) => ({
    result: r,
    originalRank: r.rank,
    newRank: r.reranked_rank!,
    delta: r.rank - r.reranked_rank!,
    scoreDelta: (r.reranker_score ?? 0) - r.score,
  }));

  // Sort by new rank
  const sortedChanges = [...changes].sort((a, b) => a.newRank - b.newRank);

  // Stats
  const promoted = changes.filter((c) => c.delta > 0).length;
  const demoted = changes.filter((c) => c.delta < 0).length;
  const unchanged = changes.filter((c) => c.delta === 0).length;
  const avgScoreChange =
    changes.reduce((sum, c) => sum + c.scoreDelta, 0) / changes.length;

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard
          label="Promoted"
          value={promoted}
          color="text-emerald-500"
          icon={<ArrowUp className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Demoted"
          value={demoted}
          color="text-red-500"
          icon={<ArrowDown className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Unchanged"
          value={unchanged}
          color="text-muted-foreground"
          icon={<Minus className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Avg Score Δ"
          value={avgScoreChange >= 0 ? `+${avgScoreChange.toFixed(3)}` : avgScoreChange.toFixed(3)}
          color={avgScoreChange >= 0 ? "text-emerald-500" : "text-red-500"}
        />
      </div>

      {/* Reranking visualization */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Ranking Changes
        </p>
        {sortedChanges.map((change, idx) => (
          <RankChangeRow key={change.result.id} change={change} />
        ))}
      </div>

      {/* Score distribution */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Score Comparison
        </p>
        <div className="rounded-lg border border-border bg-card p-4 space-y-3">
          {sortedChanges.map((change) => (
            <ScoreComparisonRow key={change.result.id} change={change} />
          ))}
        </div>
      </div>
    </div>
  );
}

function RankChangeRow({ change }: { change: RankChange }) {
  const isPromoted = change.delta > 0;
  const isDemoted = change.delta < 0;
  const isUnchanged = change.delta === 0;

  return (
    <div
      className={`rounded-lg border p-3 transition-all ${
        isPromoted
          ? "border-emerald-500/30 bg-emerald-500/5"
          : isDemoted
          ? "border-red-500/30 bg-red-500/5"
          : "border-border bg-card"
      }`}
    >
      <div className="flex items-center gap-3">
        {/* Original rank */}
        <div className="flex items-center gap-2 w-16 shrink-0">
          <div className="h-7 w-7 rounded-full bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground">
            {change.originalRank}
          </div>
        </div>

        {/* Arrow indicator */}
        <div className="shrink-0">
          {isPromoted ? (
            <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-500/10">
              <ArrowUp className="h-3.5 w-3.5 text-emerald-500" />
              <span className="text-xs font-semibold text-emerald-500">
                +{change.delta}
              </span>
            </div>
          ) : isDemoted ? (
            <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-red-500/10">
              <ArrowDown className="h-3.5 w-3.5 text-red-500" />
              <span className="text-xs font-semibold text-red-500">
                {change.delta}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1 px-2 py-1 rounded-full bg-muted/50">
              <Minus className="h-3.5 w-3.5 text-muted-foreground" />
              <span className="text-xs font-semibold text-muted-foreground">
                0
              </span>
            </div>
          )}
        </div>

        {/* New rank */}
        <div className="flex items-center gap-2 w-16 shrink-0">
          <div
            className={`h-7 w-7 rounded-full flex items-center justify-center text-xs font-semibold ${
              change.result.selected
                ? "bg-violet-500 text-white"
                : "bg-primary/20 text-primary"
            }`}
          >
            {change.newRank}
          </div>
        </div>

        {/* Document info */}
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-foreground truncate">
            {change.result.document_name}
          </p>
          <p className="text-xs text-muted-foreground truncate mt-0.5">
            {change.result.content}
          </p>
        </div>

        {/* Score change */}
        <div className="text-right shrink-0">
          <div className="text-xs text-muted-foreground">Score</div>
          <div className="text-sm font-semibold font-mono tabular-nums text-foreground">
            {change.result.reranker_score?.toFixed(3) ?? "—"}
          </div>
          <div
            className={`text-xs font-medium ${
              change.scoreDelta >= 0 ? "text-emerald-500" : "text-red-500"
            }`}
          >
            {change.scoreDelta >= 0 ? "+" : ""}
            {change.scoreDelta.toFixed(3)}
          </div>
        </div>
      </div>
    </div>
  );
}

function ScoreComparisonRow({ change }: { change: RankChange }) {
  const originalScore = change.result.score;
  const rerankerScore = change.result.reranker_score ?? 0;
  const maxScore = Math.max(originalScore, rerankerScore);

  const originalPercent = (originalScore / maxScore) * 100;
  const rerankerPercent = (rerankerScore / maxScore) * 100;

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <div className="h-6 w-6 rounded-full bg-muted flex items-center justify-center text-xs font-semibold text-muted-foreground shrink-0">
          {change.newRank}
        </div>
        <span className="text-xs text-foreground truncate flex-1">
          {change.result.document_name}
        </span>
      </div>

      {/* Original score bar */}
      <div className="space-y-0.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Original</span>
          <span className="font-mono tabular-nums text-foreground">
            {originalScore.toFixed(4)}
          </span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500/60 rounded-full transition-all"
            style={{ width: `${originalPercent}%` }}
          />
        </div>
      </div>

      {/* Reranker score bar */}
      <div className="space-y-0.5">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Reranked</span>
          <span className="font-mono tabular-nums text-foreground">
            {rerankerScore.toFixed(4)}
          </span>
        </div>
        <div className="h-1.5 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-purple-500 rounded-full transition-all"
            style={{ width: `${rerankerPercent}%` }}
          />
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
  icon,
}: {
  label: string;
  value: string | number;
  color?: string;
  icon?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <div className={`flex items-center gap-1.5 mt-1 ${color || "text-foreground"}`}>
        {icon}
        <p className="text-base font-semibold tabular-nums">{value}</p>
      </div>
    </div>
  );
}
