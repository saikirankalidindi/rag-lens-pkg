import { Suspense } from "react";
import { TracesTable } from "@/components/traces/TracesTable";

interface TracesPageProps {
  params: Promise<{ projectId: string }>;
}

export default async function TracesPage({ params }: TracesPageProps) {
  const { projectId } = await params;

  return (
    <div className="p-6 space-y-5">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Traces</h1>
        <p className="text-sm text-muted-foreground mt-1">
          All RAG pipeline requests for this project.
        </p>
      </div>

      <Suspense
        fallback={
          <div className="rounded-lg border border-border bg-card h-64 animate-pulse" />
        }
      >
        <TracesTable projectId={projectId} />
      </Suspense>
    </div>
  );
}
