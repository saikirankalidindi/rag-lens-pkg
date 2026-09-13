"use client";

import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useProject } from "@/hooks/use-raglens";
import { projectsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useToast } from "@/components/ui/toast";

export default function SettingsPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const { data: project } = useProject(projectId);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const queryClient = useQueryClient();
  const { toast } = useToast();
  useEffect(() => { if (project) { setName(project.name); setDescription(project.description ?? ""); } }, [project]);
  const update = useMutation({
    mutationFn: () => projectsApi.update(projectId, { name: name.trim(), description: description.trim() }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["projects"] });
      toast({ title: "Project settings saved", variant: "success" });
    },
  });
  return <div className="p-6 max-w-2xl space-y-6">
    <div><h1 className="text-xl font-semibold">Settings</h1><p className="text-sm text-muted-foreground">Update your project details.</p></div>
    <form className="rounded-lg border border-border bg-card p-6 space-y-4" onSubmit={(e) => { e.preventDefault(); if (name.trim()) update.mutate(); }}>
      <div className="space-y-2"><Label htmlFor="settings-name">Project name</Label><Input id="settings-name" value={name} onChange={(e) => setName(e.target.value)} required maxLength={255} /></div>
      <div className="space-y-2"><Label htmlFor="settings-description">Description</Label><Input id="settings-description" value={description} onChange={(e) => setDescription(e.target.value)} maxLength={1000} /></div>
      {update.error && <p role="alert" className="text-destructive">{update.error.message}</p>}
      <Button type="submit" disabled={update.isPending || !name.trim()}>{update.isPending ? "Saving…" : "Save changes"}</Button>
    </form>
    <p className="text-sm text-muted-foreground">Project ID: <code>{projectId}</code></p>
    <Link href={`/projects/${projectId}/settings/api-keys`} className="text-primary underline">Manage API keys</Link>
  </div>;
}
