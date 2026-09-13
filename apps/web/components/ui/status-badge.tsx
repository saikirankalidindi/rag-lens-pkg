import { cn } from "@/lib/utils";
import type { TraceStatus } from "@/lib/types";

interface StatusBadgeProps {
  status: TraceStatus;
  className?: string;
}

const STATUS_CONFIG: Record<
  TraceStatus,
  { label: string; classes: string; dot: string }
> = {
  success: {
    label: "Success",
    classes:
      "bg-emerald-500/10 text-emerald-400 ring-emerald-500/20",
    dot: "bg-emerald-400",
  },
  warning: {
    label: "Warning",
    classes: "bg-amber-500/10 text-amber-400 ring-amber-500/20",
    dot: "bg-amber-400",
  },
  error: {
    label: "Error",
    classes: "bg-red-500/10 text-red-400 ring-red-500/20",
    dot: "bg-red-400",
  },
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const cfg = STATUS_CONFIG[status] ?? STATUS_CONFIG.success;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded px-1.5 py-0.5 text-[11px] font-medium ring-1 ring-inset",
        cfg.classes,
        className
      )}
    >
      <span className={cn("h-1.5 w-1.5 rounded-full", cfg.dot)} />
      {cfg.label}
    </span>
  );
}
