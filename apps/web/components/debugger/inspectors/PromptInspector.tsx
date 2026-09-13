"use client";

import { Copy, FileText, Hash } from "lucide-react";
import { useToast } from "@/components/ui/toast";
import { useState } from "react";
import type { Span } from "@/lib/types";

interface PromptInspectorProps {
  span: Span;
}

export function PromptInspector({ span }: PromptInspectorProps) {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);

  const prompt = (span.output?.prompt ?? span.input?.prompt) as
    | string
    | undefined;
  const messages = (span.output?.messages ?? span.input?.messages) as
    | Array<{ role: string; content: string }>
    | undefined;
  const tokenCount = (span.attributes?.token_count as number | undefined) ?? null;
  const templateVars = (span.attributes?.template_variables as
    | Record<string, unknown>
    | undefined) ?? null;

  if (!prompt && !messages) {
    return (
      <div className="rounded-md border border-border bg-muted/10 px-4 py-8 text-center">
        <p className="text-sm text-muted-foreground">
          No prompt data available
        </p>
      </div>
    );
  }

  const handleCopy = async () => {
    const textToCopy = messages
      ? messages.map((m) => `${m.role}: ${m.content}`).join("\n\n")
      : prompt || "";
    try {
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { toast({ title: "Could not copy prompt", variant: "error" }); }
  };

  return (
    <div className="space-y-4">
      {/* Stats */}
      <div className="flex gap-3">
        <StatCard
          label="Token Count"
          value={tokenCount ? tokenCount.toLocaleString() : "—"}
          icon={<FileText className="h-3.5 w-3.5" />}
        />
        {messages && (
          <StatCard
            label="Messages"
            value={messages.length}
            icon={<Hash className="h-3.5 w-3.5" />}
          />
        )}
      </div>

      {/* Template variables */}
      {templateVars && Object.keys(templateVars).length > 0 && (
        <div className="space-y-2">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            Template Variables
          </p>
          <div className="rounded-lg border border-border bg-card">
            {Object.entries(templateVars).map(([key, value], idx, arr) => (
              <div
                key={key}
                className={`px-4 py-2.5 flex items-start gap-4 ${
                  idx !== arr.length - 1 ? "border-b border-border" : ""
                }`}
              >
                <span className="text-sm text-muted-foreground min-w-[100px] shrink-0 font-mono">
                  {key}
                </span>
                <span className="text-sm text-foreground break-words flex-1">
                  {typeof value === "string" ? value : JSON.stringify(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Prompt content */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {messages ? "Messages" : "Prompt"}
          </p>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-primary/10 hover:bg-primary/20 text-primary transition-colors text-xs font-medium"
          >
            <Copy className="h-3 w-3" />
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>

        <div className="rounded-lg border border-border bg-card overflow-hidden">
          {messages ? (
            <div className="divide-y divide-border">
              {messages.map((message, idx) => (
                <MessageBlock key={idx} message={message} />
              ))}
            </div>
          ) : (
            <div className="p-4">
              <pre className="text-sm text-foreground leading-relaxed whitespace-pre-wrap font-mono">
                {prompt?.split(/(\{\{[^}]+\}\}|\{[a-zA-Z_][a-zA-Z0-9_]*\})/g).map((part, i) =>
                  /^\{/.test(part) ? <span key={i} className="text-amber-400">{part}</span> : part)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function MessageBlock({ message }: { message: { role: string; content: string } }) {
  const roleColors: Record<string, string> = {
    system: "bg-blue-500/10 text-blue-500 border-blue-500/20",
    user: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
    assistant: "bg-violet-500/10 text-violet-500 border-violet-500/20",
    function: "bg-amber-500/10 text-amber-500 border-amber-500/20",
    tool: "bg-orange-500/10 text-orange-500 border-orange-500/20",
  };

  const roleColor =
    roleColors[message.role] || "bg-muted/50 text-muted-foreground border-border";

  return (
    <div className="p-4 space-y-2">
      <div
        className={`inline-flex items-center px-2 py-1 rounded border text-xs font-semibold uppercase tracking-wider ${roleColor}`}
      >
        {message.role}
      </div>
      <div className="bg-muted/20 rounded-lg p-3">
        <pre className="text-sm text-foreground leading-relaxed whitespace-pre-wrap font-sans">
          {message.content}
        </pre>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string | number;
  icon?: React.ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border bg-card px-3 py-2">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {label}
      </p>
      <div className="flex items-center gap-1.5 mt-1 text-foreground">
        {icon}
        <p className="text-base font-semibold tabular-nums">{value}</p>
      </div>
    </div>
  );
}
