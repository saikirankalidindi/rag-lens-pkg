"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { useProject } from "@/hooks/use-raglens";
import { Sidebar } from "@/components/layout/Sidebar";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";

interface ClientProjectLayoutProps {
  projectId: string;
  children: React.ReactNode;
}

export function ClientProjectLayout({
  projectId,
  children,
}: ClientProjectLayoutProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout } = useAuth();
  const base = `/projects/${projectId}`;
  const { data: project, error, isLoading, refetch } = useProject(projectId);

  return (
    <ProtectedRoute>
      <div className="flex flex-col md:flex-row h-screen overflow-hidden">
        <header className="md:hidden flex flex-wrap items-center gap-3 border-b border-border p-3 text-sm">
          <Link href="/projects" className="text-primary">All projects</Link>
          <select aria-label="Project navigation" className="min-w-0 flex-1 rounded border border-border bg-card p-1" value={pathname.includes("/traces") ? `${base}/traces` : pathname} onChange={(e) => router.push(e.target.value)}>
            <option value={base}>Overview</option><option value={`${base}/traces`}>Traces</option><option value={`${base}/settings`}>Settings</option><option value={`${base}/settings/api-keys`}>API Keys</option>
          </select>
          <button onClick={logout}>Sign out</button>
        </header>
        <Sidebar
          projectId={projectId}
          projectName={project?.name ?? "Loading…"}
        />
        <main className="min-w-0 flex-1 overflow-y-auto bg-background">{error ? <div role="alert" className="p-6">{error.message}<button className="ml-4 underline" onClick={() => refetch()}>Retry</button></div> : isLoading ? <p className="p-6">Loading project…</p> : children}</main>
      </div>
    </ProtectedRoute>
  );
}
