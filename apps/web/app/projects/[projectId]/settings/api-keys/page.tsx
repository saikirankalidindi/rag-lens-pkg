"use client";

import React, { useState } from "react";
import { Copy, Key, Loader2, Plus, Trash2, Check } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiKeysApi } from "@/lib/api";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ApiKeysPageProps {
  params: Promise<{ projectId: string }>;
}

export default function ApiKeysPage({ params }: ApiKeysPageProps) {
  const [projectId, setProjectId] = useState<string>("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null);
  const { toast } = useToast();

  // Unwrap params
  React.useEffect(() => {
    params.then((p) => setProjectId(p.projectId));
  }, [params]);

  const queryClient = useQueryClient();

  // Fetch API keys
  const { data: apiKeys, isLoading, error, refetch } = useQuery({
    queryKey: ["api-keys", projectId],
    queryFn: () => apiKeysApi.list(projectId),
    enabled: !!projectId,
  });

  // Create API key mutation
  const createMutation = useMutation({
    mutationFn: (name: string) => apiKeysApi.create(projectId, name),
    onSuccess: (data) => {
      setIsCreateDialogOpen(false);
      setCreatedKey(data.raw_key);
      setNewKeyName("");
      queryClient.invalidateQueries({ queryKey: ["api-keys", projectId] });
      toast({
        title: "API key created",
        description: "Your new API key has been created. Make sure to copy it now!",
        variant: "success",
      });
    },
    onError: (error) => {
      toast({
        title: "Failed to create API key",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "error",
      });
    },
  });

  // Revoke API key mutation
  const revokeMutation = useMutation({
    mutationFn: (keyId: string) => apiKeysApi.revoke(projectId, keyId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys", projectId] });
      toast({
        title: "API key revoked",
        description: "The API key has been revoked and can no longer be used.",
        variant: "success",
      });
    },
    onError: (error) => {
      toast({
        title: "Failed to revoke API key",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "error",
      });
    },
  });

  const handleCreateKey = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKeyName.trim()) return;
    createMutation.mutate(newKeyName.trim());
  };

  const handleCopyKey = async (key: string, keyId: string) => {
    try {
      await navigator.clipboard.writeText(key);
      setCopiedKeyId(keyId);
      setTimeout(() => setCopiedKeyId(null), 2000);
      toast({ title: "Copied to clipboard", variant: "success" });
    } catch {
      toast({ title: "Could not copy", description: "Select the key and copy it manually.", variant: "error" });
    }
  };

  const handleCloseCreatedDialog = () => {
    setCreatedKey(null);
    setIsCreateDialogOpen(false);
  };

  if (!projectId) {
    return (
      <div className="flex items-center justify-center p-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6 max-w-4xl">
      {/* Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-semibold text-foreground">API Keys</h1>
        <p className="text-sm text-muted-foreground">
          Manage API keys for trace ingestion from your RAG applications
        </p>
      </div>

      {/* Info box */}
      <div className="rounded-lg border border-blue-500/30 bg-blue-500/5 p-4">
        <p className="text-sm text-foreground leading-relaxed">
          <strong className="font-semibold">Important:</strong> API keys are
          shown only once after creation. Store them securely — they cannot be
          retrieved later.
        </p>
      </div>

      {/* Create button */}
      <Button onClick={() => setIsCreateDialogOpen(true)}>
        <Plus className="h-4 w-4 mr-2" />
        Create API Key
      </Button>

      {/* API Keys list */}
      {error ? <p role="alert">{error.message} <Button variant="outline" onClick={() => refetch()}>Retry</Button></p> : isLoading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : apiKeys && apiKeys.length > 0 ? (
        <div className="rounded-lg border border-border overflow-x-auto">
          <table className="w-full">
            <thead className="bg-muted/50">
              <tr className="text-left text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                <th className="px-4 py-3">Name</th>
                <th className="px-4 py-3">Key</th>
                <th className="px-4 py-3">Created</th>
                <th className="px-4 py-3">Last Used</th>
                <th className="px-4 py-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {apiKeys.map((key) => (
                <tr key={key.id} className="hover:bg-muted/30 transition-colors">
                  <td className="px-4 py-3 text-sm font-medium text-foreground">
                    {key.name}
                  </td>
                  <td className="px-4 py-3">
                    <code className="text-xs text-muted-foreground font-mono bg-muted px-2 py-1 rounded">
                      {key.key_prefix}•••••••••••••••
                    </code>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {new Date(key.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    {key.last_used_at
                      ? new Date(key.last_used_at).toLocaleDateString()
                      : "Never"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {key.revoked_at ? (
                      <span className="text-xs text-red-500 font-medium">
                        Revoked
                      </span>
                    ) : (
                      <Button
                        aria-label={`Revoke ${key.name}`}
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          if (
                            confirm(
                              `Revoke API key "${key.name}"? This cannot be undone.`
                            )
                          ) {
                            revokeMutation.mutate(key.id);
                          }
                        }}
                        disabled={revokeMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-12 space-y-4 rounded-lg border border-dashed border-border">
          <div className="rounded-full bg-muted p-4">
            <Key className="h-8 w-8 text-muted-foreground" />
          </div>
          <div className="text-center space-y-2">
            <h3 className="text-lg font-semibold text-foreground">
              No API keys yet
            </h3>
            <p className="text-sm text-muted-foreground max-w-sm">
              Create an API key to start sending traces from your application
            </p>
          </div>
        </div>
      )}

      {/* Create API Key Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create API Key</DialogTitle>
            <DialogDescription>
              Give your API key a descriptive name to help identify its purpose.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleCreateKey}>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="keyName">Key Name</Label>
                <Input
                  id="keyName"
                  placeholder="e.g., Production, Development, CI/CD"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  required
                  maxLength={255}
                  autoFocus
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsCreateDialogOpen(false)}
              >
                Cancel
              </Button>
              <Button type="submit" disabled={createMutation.isPending || !newKeyName.trim()}>
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  "Create Key"
                )}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Show Created Key Dialog */}
      <Dialog open={!!createdKey} onOpenChange={handleCloseCreatedDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>API Key Created</DialogTitle>
            <DialogDescription>
              Copy your API key now. You won&apos;t be able to see it again!
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Your API Key</Label>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-sm font-mono bg-muted px-3 py-2 rounded border border-border break-all">
                  {createdKey}
                </code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() =>
                    createdKey && handleCopyKey(createdKey, "created")
                  }
                >
                  {copiedKeyId === "created" ? (
                    <Check className="h-4 w-4 text-emerald-500" />
                  ) : (
                    <Copy className="h-4 w-4" />
                  )}
                </Button>
              </div>
            </div>
            <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3">
              <p className="text-sm text-foreground">
                <strong className="font-semibold">Store it safely:</strong> This
                key will not be shown again. If you lose it, you&apos;ll need to
                create a new one.
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button onClick={handleCloseCreatedDialog}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
