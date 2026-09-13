import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { TraceDebugger } from "@/components/debugger/TraceDebugger";

interface TracePageProps {
  params: Promise<{ projectId: string; traceId: string }>;
}

export default async function TracePage({ params }: TracePageProps) {
  const { projectId, traceId } = await params;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Breadcrumb nav */}
      <div className="flex items-center gap-2 px-5 py-3 border-b border-border shrink-0">
        <Link
          href={`/projects/${projectId}/traces`}
          className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
        >
          <ChevronLeft className="h-3.5 w-3.5" />
          Traces
        </Link>
      </div>

      {/* Full-height debugger */}
      <div className="flex-1 min-h-0">
        <TraceDebugger projectId={projectId} traceId={traceId} />
      </div>
    </div>
  );
}
