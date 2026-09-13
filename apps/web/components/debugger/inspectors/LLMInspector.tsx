"use client";

import { Activity, Cpu, DollarSign, Zap } from "lucide-react";
import type { Span, TraceMetrics } from "@/lib/types";
import { formatCost, formatDuration } from "@/lib/utils";

interface LLMInspectorProps {
  span: Span;
  metrics?: TraceMetrics | null;
}

export function LLMInspector({ span, metrics }: LLMInspectorProps) {
  const attrs = span.attributes ?? {};
  const output = (span.output ?? {}) as Record<string, unknown>;

  // Extract LLM metadata
  const provider = (attrs.provider as string | undefined) ?? "—";
  const model = (attrs.model as string | undefined) ?? "—";
  const temperature = attrs.temperature as number | undefined;
  const maxTokens = attrs.max_tokens as number | undefined;
  const topP = attrs.top_p as number | undefined;
  const frequencyPenalty = attrs.frequency_penalty as number | undefined;
  const presencePenalty = attrs.presence_penalty as number | undefined;
  const finishReason = (output.finish_reason as string | undefined) ?? "—";

  // Token metrics
  const inputTokens = typeof attrs.input_tokens === "number" ? attrs.input_tokens : metrics?.input_tokens ?? null;
  const outputTokens = typeof attrs.output_tokens === "number" ? attrs.output_tokens : metrics?.output_tokens ?? null;
  const totalTokens = inputTokens != null && outputTokens != null ? inputTokens + outputTokens : metrics?.total_tokens ?? null;
  const cost = metrics?.estimated_cost ?? null;

  // Performance metrics
  const latency = span.duration_ms;
  const tokensPerSecond =
    outputTokens && latency ? (outputTokens / (latency / 1000)).toFixed(2) : null;

  return (
    <div className="space-y-4">
      {/* Performance metrics */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard
          label="Latency"
          value={formatDuration(latency)}
          icon={<Activity className="h-3.5 w-3.5" />}
          color={latency > 5000 ? "text-amber-500" : undefined}
        />
        <StatCard
          label="Tokens/sec"
          value={tokensPerSecond ?? "—"}
          icon={<Zap className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Total Tokens"
          value={totalTokens?.toLocaleString() ?? "—"}
          icon={<Cpu className="h-3.5 w-3.5" />}
        />
        <StatCard
          label="Est. Cost"
          value={cost != null ? formatCost(cost) : "—"}
          icon={<DollarSign className="h-3.5 w-3.5" />}
        />
      </div>

      {/* Token breakdown */}
      <>
        {(inputTokens != null || outputTokens != null) && (
          <div className="space-y-2">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              Token Usage
            </p>
            <div className="rounded-lg border border-border bg-card p-4">
              <div className="space-y-3">
                {/* Input tokens */}
                {inputTokens != null && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Input</span>
                      <span className="font-semibold text-foreground tabular-nums">
                        {inputTokens.toLocaleString()} tokens
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{
                          width: `${
                            totalTokens
                              ? (inputTokens / totalTokens) * 100
                              : 100
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Output tokens */}
                {outputTokens != null && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">Output</span>
                      <span className="font-semibold text-foreground tabular-nums">
                        {outputTokens.toLocaleString()} tokens
                      </span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className="h-full bg-violet-500 rounded-full"
                        style={{
                          width: `${
                            totalTokens
                              ? (outputTokens / totalTokens) * 100
                              : 100
                          }%`,
                        }}
                      />
                    </div>
                  </div>
                )}

                {/* Ratio */}
                {inputTokens != null && outputTokens != null && (
                  <div className="pt-2 border-t border-border">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-muted-foreground">
                        Input/Output Ratio
                      </span>
                      <span className="font-semibold text-foreground tabular-nums">
                        {(inputTokens / outputTokens).toFixed(2)}:1
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </>

      {/* Model configuration */}
      <div className="space-y-2">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Model Configuration
        </p>
        <div className="rounded-lg border border-border bg-card">
          <ConfigRow label="Provider" value={provider} />
          <ConfigRow label="Model" value={model} />
          {temperature != null && (
            <ConfigRow label="Temperature" value={temperature.toString()} />
          )}
          {maxTokens != null && (
            <ConfigRow label="Max Tokens" value={maxTokens.toLocaleString()} />
          )}
          {topP != null && <ConfigRow label="Top P" value={topP.toString()} />}
          {frequencyPenalty != null && (
            <ConfigRow
              label="Frequency Penalty"
              value={frequencyPenalty.toString()}
            />
          )}
          {presencePenalty != null && (
            <ConfigRow
              label="Presence Penalty"
              value={presencePenalty.toString()}
            />
          )}
          <ConfigRow label="Finish Reason" value={finishReason} isLast />
        </div>
      </div>

      {/* Response preview */}
      {output.content != null && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Response Preview
          </p>
          <div className="rounded-lg border border-border bg-muted/10 p-4">
            <p className="text-sm text-foreground leading-relaxed line-clamp-6">
              {String(output.content)}
            </p>
          </div>
        </div>
      )}

      {/* Additional metadata */}
      {Object.keys(attrs).length > 0 && (
        <details className="group">
          <summary className="text-xs font-semibold text-muted-foreground uppercase tracking-wider cursor-pointer hover:text-foreground transition-colors">
            Additional Metadata
          </summary>
          <div className="mt-2 rounded-lg border border-border bg-card p-3">
            <pre className="text-xs text-foreground font-mono overflow-x-auto">
              {JSON.stringify(attrs, null, 2)}
            </pre>
          </div>
        </details>
      )}
    </div>
  );
}

function ConfigRow({
  label,
  value,
  isLast = false,
}: {
  label: string;
  value: string;
  isLast?: boolean;
}) {
  return (
    <div
      className={`flex items-center justify-between px-4 py-2.5 ${
        !isLast ? "border-b border-border" : ""
      }`}
    >
      <span className="text-sm text-muted-foreground">{label}</span>
      <span className="text-sm font-medium text-foreground font-mono">
        {value}
      </span>
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
