"use client";

import * as React from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";

type ToastVariant = "default" | "success" | "error" | "warning";

interface Toast {
  id: string;
  title?: string;
  description?: string;
  variant?: ToastVariant;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  toast: (props: Omit<Toast, "id">) => void;
  dismiss: (id: string) => void;
}

const ToastContext = React.createContext<ToastContextType | undefined>(
  undefined
);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = React.useState<Toast[]>([]);

  const toast = React.useCallback((props: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(7);
    const newToast: Toast = {
      id,
      variant: "default",
      duration: 5000,
      ...props,
    };

    setToasts((prev) => [...prev, newToast]);

    // Auto dismiss after duration
    if (newToast.duration) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, newToast.duration);
    }
  }, []);

  const dismiss = React.useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, toast, dismiss }}>
      {children}
      <ToastContainer toasts={toasts} dismiss={dismiss} />
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = React.useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

function ToastContainer({
  toasts,
  dismiss,
}: {
  toasts: Toast[];
  dismiss: (id: string) => void;
}) {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-0 right-0 z-[100] flex max-h-screen w-full flex-col-reverse gap-2 p-4 sm:top-auto sm:bottom-0 sm:right-0 sm:flex-col sm:max-w-[420px]">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} dismiss={dismiss} />
      ))}
    </div>
  );
}

function ToastItem({
  toast,
  dismiss,
}: {
  toast: Toast;
  dismiss: (id: string) => void;
}) {
  const variantStyles: Record<ToastVariant, string> = {
    default: "border-border bg-card text-foreground",
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-500",
    error: "border-red-500/30 bg-red-500/10 text-red-500",
    warning: "border-amber-500/30 bg-amber-500/10 text-amber-500",
  };

  return (
    <div
      className={cn(
        "group pointer-events-auto relative flex w-full items-start gap-3 overflow-hidden rounded-lg border p-4 shadow-lg transition-all animate-in slide-in-from-top-full sm:slide-in-from-bottom-full",
        variantStyles[toast.variant || "default"]
      )}
    >
      <div className="flex-1 space-y-1">
        {toast.title && (
          <div className="text-sm font-semibold">{toast.title}</div>
        )}
        {toast.description && (
          <div className="text-sm opacity-90">{toast.description}</div>
        )}
      </div>
      <button
        onClick={() => dismiss(toast.id)}
        className="rounded-md p-1 opacity-70 transition-opacity hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2"
      >
        <X className="h-4 w-4" />
        <span className="sr-only">Close</span>
      </button>
    </div>
  );
}
