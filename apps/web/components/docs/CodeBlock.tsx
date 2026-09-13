"use client";

import { useState } from "react";
import { Check, Copy } from "lucide-react";

export function CodeBlock({ code, label = "Python" }: { code: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copyCode() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return <div className="overflow-hidden rounded-xl border border-white/10 bg-[#0a0c10]"><div className="flex items-center justify-between border-b border-white/[0.07] px-4 py-2 text-[11px] text-zinc-500"><span>{label}</span><button type="button" onClick={copyCode} className="inline-flex items-center gap-1.5 rounded px-2 py-1 text-zinc-400 hover:bg-white/10 hover:text-white" aria-label={`Copy ${label} example`}>{copied ? <Check size={13} /> : <Copy size={13} />} {copied ? "Copied" : "Copy"}</button></div><pre className="max-h-[520px] overflow-auto p-4 text-[12px] leading-6 text-zinc-300"><code>{code}</code></pre></div>;
}
