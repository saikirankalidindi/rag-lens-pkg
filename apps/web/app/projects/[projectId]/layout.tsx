import { ClientProjectLayout } from "@/components/layout/ClientProjectLayout";

interface ProjectLayoutProps {
  children: React.ReactNode;
  params: Promise<{ projectId: string }>;
}

export default async function ProjectLayout({
  children,
  params,
}: ProjectLayoutProps) {
  const { projectId } = await params;

  return (
    <ClientProjectLayout projectId={projectId}>
      {children}
    </ClientProjectLayout>
  );
}
