"use client";

import { FileText, Layers } from "lucide-react";
import { useToast } from "@/components/ui/toast";
import type { Span } from "@/lib/types";

interface ContextInspectorProps {
  span: Span;
}

export function ContextInspector({ span }: ContextInspectorProps) {
  const { toast } = useToast();
  const context = span.output?.context as string | undefined;
  const chunks = span.output?.chunks as
    | Array<{ content: string; source?: string }>
    | undefined;
  const tokenCount = (span.attributes?.token_count as number | undefined) ?? null;
  const maxTokens = (span.attributes?.max_tokens as number | undefined) ?? null;

  if (!context && !chunks) {
    return (
      <div className="rounded-md border border-border bg-muted/10 px-4 py-8 text-center">
        <p className="text-sm text-muted-foreground">
          No context data available
        </p>
      </div>
    );
  }

  const utilizationPercent =
    tokenCount && maxTokens ? (tokenCount / maxTokens) * 100 : null;

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard
          label="Token Count"
          value={tokenCount ? tokenCount.toLocaleString() : "—"}
          icon={<FileText className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Max Tokens"
          value={maxTokens ? maxTokens.toLocaleString() : "—"}
          icon={<Layers className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Utilization"
          value={
            utilizationPercent != null ? `${utilizationPercent.toFixed(1)}%` : "—"
          }
          color={
            utilizationPercent != null && utilizationPercent > 80
              ? "text-amber-500"
              : undefined
          }
        />
      </div>

      {/* Context window visualization */}
      {utilizationPercent != null && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Context Window Usage
          </p>
          <div className="rounded-lg border border-border bg-card p-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  {tokenCount?.toLocaleString()} / {maxTokens?.toLocaleString()}{" "}
                  tokens
                </span>
                <span
                  className={`font-semibold ${
                    utilizationPercent > 80
                      ? "text-amber-500"
                      : "text-foreground"
                  }`}
                >
                  {utilizationPercent.toFixed(1)}%
                </span>
              </div>
              <div className="h-3 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all ${
                    utilizationPercent > 80
                      ? "bg-amber-500"
                      : utilizationPercent > 60
                      ? "bg-blue-500"
                      : "bg-emerald-500"
                  }`}
                  style={{ width: `${Math.min(utilizationPercent, 100)}%` }}
                />
              </div>
              {utilizationPercent > 80 && (
                <p className="text-xs text-amber-500 flex items-center gap-1.5">
                  <span className="font-semibold">⚠</span>
                  High context utilization may impact response quality
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Individual chunks */}
      {chunks && chunks.length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Context Chunks ({chunks.length})
          </p>
          <div className="space-y-2">
            {chunks.map((chunk, idx) => (
              <div
                key={idx}
                className="rounded-lg border border-border bg-card p-3 space-y-2"
              >
                <div className="flex items-center gap-2">
                  <div className="h-6 w-6 rounded bg-primary/10 flex items-center justify-center text-xs font-semibold text-primary">
                    {idx + 1}
                  </div>
                  {chunk.source && (
                    <span className="text-xs text-muted-foreground truncate">
                      {chunk.source}
                    </span>
                  )}
                </div>
                <div className="rounded bg-muted/30 px-3 py-2">
                  <p className="text-sm text-foreground leading-relaxed whitespace-pre-wrap">
                    {chunk.content}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Full assembled context */}
      {context && (
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Assembled Context
            </p>
            <button
              onClick={async () => { try { await navigator.clipboard.writeText(context); toast({ title: "Context copied", variant: "success" }); } catch { toast({ title: "Could not copy context", variant: "error" }); } }}
              className="text-xs text-primary hover:text-primary/80 transition-colors"
            >
              Copy
            </button>
          </div>
          <div className="rounded-lg border border-border bg-muted/10 p-4 max-h-96 overflow-y-auto">
            <pre className="text-sm text-foreground leading-relaxed whitespace-pre-wrap font-sans">
              {context}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <div
        className={`flex items-center gap-1.5 mt-1 ${color || "text-foreground"}`}
      >
        {icon}
        <p className="text-base font-semibold tabular-nums">{value}</p>
      </div>
    </div>
  );
}
