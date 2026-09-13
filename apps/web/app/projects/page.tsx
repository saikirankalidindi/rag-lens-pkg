"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  ChevronRight,
  CircleHelp,
  Clock3,
  FolderKanban,
  Layers3,
  LogOut,
  Plus,
  Search,
  Terminal,
  X,
} from "lucide-react";
import { projectsApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { formatDuration, formatRelativeTime, formatTokens } from "@/lib/utils";
import { useToast } from "@/components/ui/toast";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { useProjects } from "@/hooks/use-raglens";
import { Button } from "@/components/ui/button";

const normalizedName = (value: string) =>
  value.trim().replace(/\s+/g, " ").toLowerCase();
const accents = [
  "bg-cyan-400/10 text-cyan-300 border-cyan-400/20",
  "bg-violet-400/10 text-violet-300 border-violet-400/20",
  "bg-amber-400/10 text-amber-300 border-amber-400/20",
];

export default function ProjectsPage() {
  const router = useRouter();
  const { data: projects, isLoading, error, refetch } = useProjects();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("activity");
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const duplicate =
    !!name.trim() &&
    !!projects?.some(
      (project) => normalizedName(project.name) === normalizedName(name),
    );
  const create = useMutation({
    mutationFn: () =>
      projectsApi.create({
        name: name.trim(),
        description: description.trim(),
      }),
    onSuccess: async (project) => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      setOpen(false);
      setName("");
      setDescription("");
      toast({ title: "Project created", variant: "success" });
      router.push(`/projects/${project.id}`);
    },
  });
  const openCreate = () => {
    create.reset();
    setName("");
    setDescription("");
    setOpen(true);
  };
  const filtered = useMemo(
    () =>
      (projects ?? [])
        .filter((project) =>
          `${project.name} ${project.description ?? ""}`
            .toLowerCase()
            .includes(search.trim().toLowerCase()),
        )
        .sort((a, b) =>
          sort === "name"
            ? a.name.localeCompare(b.name)
            : sort === "newest"
              ? Date.parse(b.created_at) - Date.parse(a.created_at)
              : Date.parse(b.last_trace_at ?? b.created_at) -
                Date.parse(a.last_trace_at ?? a.created_at),
        ),
    [projects, search, sort],
  );
  const totalTraces =
    projects?.reduce((sum, p) => sum + (p.trace_count ?? 0), 0) ?? 0;
  const totalErrors =
    projects?.reduce((sum, p) => sum + (p.error_count ?? 0), 0) ?? 0;
  const observed =
    projects?.filter((p) => (p.trace_count ?? 0) > 0).length ?? 0;
  const latest = projects
    ?.filter((p) => p.last_trace_at)
    .sort(
      (a, b) => Date.parse(b.last_trace_at!) - Date.parse(a.last_trace_at!),
    )[0];
  const greeting =
    user?.full_name?.split(" ")[0] ?? user?.email.split("@")[0] ?? "there";
  const available = !isLoading && !error && !!projects;

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0b0d11] text-zinc-100 md:flex">
        <aside className="hidden md:flex fixed inset-y-0 left-0 w-56 flex-col border-r border-white/[0.06] bg-[#0e1015] p-5">
          <Link
            href="/projects"
            className="mb-10 flex items-center gap-2.5 text-lg font-semibold tracking-tight"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-cyan-300 text-zinc-950">
              <Layers3 className="h-[18px] w-[18px]" />
            </div>
            RAGLens
          </Link>
          <p className="mb-3 px-3 text-[10px] font-medium uppercase tracking-[.18em] text-zinc-500">
            Workspace
          </p>
          <Link
            href="/projects"
            aria-current="page"
            className="flex items-center gap-3 rounded-lg border border-white/[0.05] bg-white/[0.06] px-3 py-2.5 text-sm"
          >
            <FolderKanban className="h-4 w-4 text-cyan-300" />
            Projects
            <span className="ml-auto text-xs text-zinc-500">
              {projects?.length ?? "—"}
            </span>
          </Link>
          <Link
            href="/docs"
            className="mt-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-zinc-400 hover:bg-white/5 hover:text-white"
          >
            <BookOpen className="h-4 w-4" />
            Documentation
          </Link>
          <div className="mt-auto space-y-5">
            <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4">
              <Terminal className="mb-3 h-5 w-5 text-zinc-400" />
              <p className="text-xs font-medium">
                One trace. The full picture.
              </p>
              <p className="mt-2 text-xs leading-relaxed text-zinc-500">
                See what your pipeline retrieved, sent, and generated.
              </p>
              <Link
                href="/docs"
                className="mt-4 inline-flex items-center gap-2 text-xs text-cyan-300 hover:text-cyan-200"
              >
                SDK quickstart
                <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>
            <div className="border-t border-white/[0.06] pt-4">
              <div className="mb-3 flex items-center gap-2.5">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-violet-400/15 text-xs font-medium text-violet-300">
                  {greeting.slice(0, 2).toUpperCase()}
                </div>
                <div className="min-w-0">
                  <p className="truncate text-xs font-medium">
                    {user?.full_name || greeting}
                  </p>
                  <p className="truncate text-[11px] text-zinc-500">
                    {user?.email}
                  </p>
                </div>
              </div>
              <button
                onClick={logout}
                className="flex items-center gap-2 text-xs text-zinc-400 hover:text-white"
              >
                <LogOut className="h-3.5 w-3.5" />
                Sign out
              </button>
            </div>
          </div>
        </aside>
        <div className="min-w-0 flex-1 md:ml-56">
          <header className="flex h-16 items-center justify-between border-b border-white/[0.06] px-5 lg:px-10">
            <div className="flex items-center gap-2 text-xs text-zinc-500">
              <span className="md:hidden font-semibold text-zinc-100">
                RAGLens
              </span>
              <span className="hidden md:inline">Workspace</span>
              <ChevronRight className="h-3 w-3" />
              <span className="text-zinc-300">Projects</span>
            </div>
            <Link
              href="/docs"
              className="hidden sm:flex items-center gap-2 text-xs text-zinc-400 hover:text-white"
            >
              <CircleHelp className="h-3.5 w-3.5" />
              Quickstart guide
              <ArrowUpRight className="h-3 w-3" />
            </Link>
            <button
              onClick={logout}
              className="md:hidden text-xs text-zinc-400"
            >
              Sign out
            </button>
          </header>
          <main className="mx-auto max-w-[1400px] px-5 py-8 lg:px-10 lg:py-10">
            <div className="mb-8 flex flex-col justify-between gap-5 sm:flex-row sm:items-end">
              <div>
                <p className="mb-2 text-sm text-zinc-500">
                  {user?.full_name ? `Welcome back, ${greeting}.` : "Welcome back."}
                </p>
                <h1 className="text-3xl font-semibold tracking-tight lg:text-4xl">
                  Your projects<span className="text-cyan-300">.</span>
                </h1>
                <p className="mt-3 max-w-lg text-sm leading-relaxed text-zinc-400">
                  Every pipeline, from retrieval to response. Pick up where you
                  left off.
                </p>
              </div>
              <Button
                onClick={openCreate}
                className="h-10 self-start bg-cyan-300 px-4 font-medium text-zinc-950 hover:bg-cyan-200 sm:self-auto"
              >
                <Plus className="h-4 w-4" />
                New Project
              </Button>
            </div>
            <div className="mb-9 grid grid-cols-2 gap-3 xl:grid-cols-4">
              {[
                {
                  label: "Projects",
                  value: projects?.length ?? 0,
                  sub: "In your workspace",
                  icon: FolderKanban,
                },
                {
                  label: "Traces captured",
                  value: totalTraces.toLocaleString(),
                  sub: "Across all projects",
                  icon: Activity,
                },
                {
                  label: "Projects with traces",
                  value: observed,
                  sub: "Projects with recorded activity",
                  icon: ArrowDownRight,
                },
                {
                  label: "Errors recorded",
                  value: totalErrors.toLocaleString(),
                  sub: "Across all recorded traces",
                  icon: CircleHelp,
                },
              ].map((item) => (
                <div
                  key={item.label}
                  className="rounded-xl border border-white/[0.07] bg-[#11141a] p-4 lg:p-5"
                >
                  <div className="flex items-center justify-between gap-2 text-xs text-zinc-400">
                    {item.label}
                    <item.icon className="h-4 w-4 text-zinc-600" />
                  </div>
                  <p className="mt-3 text-2xl font-semibold tabular-nums tracking-tight">
                    {available ? item.value : "—"}
                  </p>
                  <p className="mt-1.5 text-[11px] text-zinc-500">{item.sub}</p>
                </div>
              ))}
            </div>
            {latest && (
              <Link
                href={`/projects/${latest.id}/traces`}
                className="mb-8 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-cyan-300/10 bg-cyan-300/[0.03] px-5 py-3.5 text-sm hover:bg-cyan-300/[0.06]"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-cyan-300" />
                  <span className="text-zinc-400">
                    Latest activity{" "}
                    <span className="mx-1 text-zinc-600">/</span>{" "}
                    <span className="text-zinc-200">{latest.name}</span>
                  </span>
                </span>
                <span className="flex items-center gap-3 text-xs text-zinc-500">
                  {formatRelativeTime(latest.last_trace_at!)}
                  <ArrowRight className="h-4 w-4 text-cyan-300" />
                </span>
              </Link>
            )}
            <div className="mb-5 flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <h2 className="flex items-center gap-2 text-sm font-medium">
                All projects{" "}
                <span className="rounded-md border border-white/10 px-1.5 py-0.5 text-[10px] text-zinc-400">
                  {projects?.length ?? "—"}
                </span>
              </h2>
              <div className="flex gap-2">
                <div className="relative min-w-0 flex-1 sm:w-60">
                  <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-zinc-500" />
                  <input
                    aria-label="Search projects"
                    placeholder="Search projects…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="h-9 w-full rounded-lg border border-white/10 bg-[#11141a] pl-9 pr-8 text-xs outline-none placeholder:text-zinc-600 focus:border-cyan-300/50"
                  />
                  {search && (
                    <button
                      aria-label="Clear search"
                      onClick={() => setSearch("")}
                      className="absolute right-2 top-2.5"
                    >
                      <X className="h-3.5 w-3.5 text-zinc-400" />
                    </button>
                  )}
                </div>
                <select
                  aria-label="Sort projects"
                  value={sort}
                  onChange={(e) => setSort(e.target.value)}
                  className="h-9 rounded-lg border border-white/10 bg-[#11141a] px-2 text-xs text-zinc-400"
                >
                  <option value="activity">Recent activity</option>
                  <option value="newest">Newest created</option>
                  <option value="name">Name A–Z</option>
                </select>
              </div>
            </div>
            {error ? (
              <div
                role="alert"
                className="rounded-xl border border-red-400/25 bg-red-400/5 p-6 text-sm text-red-300"
              >
                {error.message}
                <Button
                  variant="outline"
                  onClick={() => refetch()}
                  className="ml-4"
                >
                  Retry
                </Button>
              </div>
            ) : isLoading ? (
              <div
                aria-label="Loading projects"
                className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3"
              >
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="h-56 animate-pulse rounded-xl border border-white/5 bg-white/[0.02]"
                  />
                ))}
              </div>
            ) : !projects?.length ? (
              <div className="flex flex-col items-center rounded-2xl border border-dashed border-white/10 bg-[#11141a] px-6 py-14 text-center">
                <div className="mb-5 flex h-14 w-14 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-300">
                  <Layers3 className="h-6 w-6" />
                </div>
                <h3 className="text-xl font-medium">No projects yet</h3>
                <p className="mb-6 mt-3 max-w-sm text-sm leading-relaxed text-zinc-500">
                  Give your pipeline a home. Create a project, connect the SDK,
                  and inspect your first trace.
                </p>
                <Button
                  className="bg-cyan-300 text-zinc-950 hover:bg-cyan-200"
                  onClick={openCreate}
                >
                  <Plus className="h-4 w-4" />
                  Create Project
                </Button>
                <Link
                  href="/docs"
                  className="mt-4 text-xs text-zinc-400 hover:text-white"
                >
                  Read the quickstart guide →
                </Link>
              </div>
            ) : !filtered.length ? (
              <div className="rounded-xl border border-white/10 py-16 text-center">
                <Search className="mx-auto mb-3 h-5 w-5 text-zinc-500" />
                <p className="text-sm">No projects match “{search}”</p>
                <button
                  className="mt-3 text-xs text-cyan-300"
                  onClick={() => setSearch("")}
                >
                  Clear search
                </button>
              </div>
            ) : (
              <div className="grid gap-4 lg:grid-cols-2 2xl:grid-cols-3">
                {filtered.map((project, index) => (
                  <button
                    key={project.id}
                    onClick={() => router.push(`/projects/${project.id}`)}
                    className="group flex min-w-0 flex-col rounded-xl border border-white/[0.08] bg-[#11141a] p-5 text-left transition duration-200 hover:-translate-y-0.5 hover:border-cyan-300/30 hover:bg-[#151921] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cyan-300/60"
                  >
                    <div className="mb-4 flex items-center justify-between">
                      <div
                        className={`flex h-10 w-10 items-center justify-center rounded-xl border ${accents[index % accents.length]}`}
                      >
                        <FolderKanban className="h-5 w-5" />
                      </div>
                      <ArrowUpRight className="h-4 w-4 text-zinc-600 transition group-hover:text-cyan-300" />
                    </div>
                    <h3 className="truncate text-base font-medium tracking-tight">
                      {project.name}
                    </h3>
                    <p className="mt-2 min-h-10 line-clamp-2 text-xs leading-5 text-zinc-500">
                      {project.description ||
                        "A dedicated space to observe and debug your RAG pipeline."}
                    </p>
                    <div className="my-5 grid grid-cols-3 divide-x divide-white/[0.06] border-y border-white/[0.06] py-3.5">
                      <div>
                        <p className="text-[10px] text-zinc-500">Traces</p>
                        <p className="mt-1 text-sm font-medium tabular-nums">
                          {(project.trace_count ?? 0).toLocaleString()}
                        </p>
                      </div>
                      <div className="pl-4">
                        <p className="text-[10px] text-zinc-500">
                          Avg. latency
                        </p>
                        <p className="mt-1 text-sm font-medium tabular-nums">
                          {project.trace_count
                            ? formatDuration(Math.round(project.avg_latency_ms ?? 0))
                            : "—"}
                        </p>
                      </div>
                      <div className="pl-4">
                        <p className="text-[10px] text-zinc-500">Tokens</p>
                        <p className="mt-1 text-sm font-medium tabular-nums">
                          {formatTokens(project.total_tokens ?? 0)}
                        </p>
                      </div>
                    </div>
                    <div className="mt-auto flex items-center justify-between gap-2 text-[11px]">
                      <span className="flex items-center gap-1.5 text-zinc-500">
                        {project.last_trace_at ? (
                          <>
                            <Clock3 className="h-3 w-3" />
                            {formatRelativeTime(project.last_trace_at)}
                          </>
                        ) : (
                          <>
                            <span className="h-1.5 w-1.5 rounded-full bg-zinc-600" />
                            No traces yet
                          </>
                        )}
                      </span>
                      <span className="flex items-center gap-1 text-zinc-400 group-hover:text-cyan-300">
                        Open project
                        <ArrowRight className="h-3 w-3" />
                      </span>
                    </div>
                  </button>
                ))}
              </div>
            )}
            <div className="mt-10 flex flex-wrap items-center justify-between gap-3 border-t border-white/[0.06] pt-5 text-[11px] text-zinc-600">
              <span>RAGLens · Observability for RAG pipelines</span>
              <Link
                href="/docs"
                className="flex items-center gap-1 hover:text-zinc-300"
              >
                Need help getting started?
                <ArrowUpRight className="h-3 w-3" />
              </Link>
            </div>
          </main>
        </div>
      </div>
      <Dialog
        open={open}
        onOpenChange={(value) => {
          if (!create.isPending) setOpen(value);
        }}
      >
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Create Project</DialogTitle>
            <DialogDescription>
              Give your pipeline a name. Project names are unique in your
              workspace.
            </DialogDescription>
          </DialogHeader>
          <form
            className="space-y-5 pt-2"
            onSubmit={(event) => {
              event.preventDefault();
              if (name.trim() && !duplicate && !create.isPending)
                create.mutate();
            }}
          >
            <div className="space-y-2">
              <Label htmlFor="project-name">Project name</Label>
              <Input
                id="project-name"
                placeholder="e.g. Customer support assistant"
                disabled={create.isPending}
                value={name}
                onChange={(e) => {
                  setName(e.target.value);
                  create.reset();
                }}
                required
                maxLength={255}
                autoFocus
                aria-invalid={duplicate}
                aria-describedby={duplicate ? "project-name-error" : undefined}
              />
              {duplicate && (
                <p
                  id="project-name-error"
                  role="alert"
                  className="text-xs text-red-400"
                >
                  A project with this name already exists. Choose a different
                  name.
                </p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="project-description">
                Description (optional)
              </Label>
              <Input
                id="project-description"
                placeholder="What does this pipeline do?"
                disabled={create.isPending}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                maxLength={1000}
              />
            </div>
            {create.error && (
              <p role="alert" className="text-sm text-red-400">
                {create.error.message}
              </p>
            )}
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                disabled={create.isPending}
                onClick={() => setOpen(false)}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="bg-cyan-300 text-zinc-950 hover:bg-cyan-200"
                disabled={!name.trim() || duplicate || create.isPending}
              >
                {create.isPending ? "Creating…" : "Create Project"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </ProtectedRoute>
  );
}
