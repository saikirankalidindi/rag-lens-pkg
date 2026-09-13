import { OverviewCharts } from "@/components/overview/OverviewCharts";
import { OverviewStats, RecentTraces } from "@/components/overview/OverviewStats";

interface OverviewPageProps {
  params: Promise<{ projectId: string }>;
}

export default async function OverviewPage({ params }: OverviewPageProps) {
  const { projectId } = await params;

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-xl font-semibold text-foreground">Overview</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Real-time stats for your RAG pipeline.
        </p>
      </div>

      <OverviewStats projectId={projectId} />

      <OverviewCharts projectId={projectId} />
      <RecentTraces projectId={projectId} />
    </div>
  );
}
