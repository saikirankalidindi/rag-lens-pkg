"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { AlertCircle, Loader2 } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      const requestedUrl = searchParams.get("returnUrl");
      const returnUrl = requestedUrl?.startsWith("/") && !requestedUrl.startsWith("//") && !requestedUrl.includes("\\") ? requestedUrl : "/projects";
      router.push(returnUrl);
    }
  }, [isAuthenticated, router, searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const response = await authApi.login({ email, password });
      
      // Use auth context to handle login
      await login(response.access_token);
      
      toast({
        title: "Welcome back!",
        description: "You have successfully signed in.",
        variant: "success",
      });
      
      // Redirect to return URL or projects
      const requestedUrl = searchParams.get("returnUrl");
      const returnUrl = requestedUrl?.startsWith("/") && !requestedUrl.startsWith("//") && !requestedUrl.includes("\\") ? requestedUrl : "/projects";
      router.push(returnUrl);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
      toast({
        title: "Login failed",
        description: message,
        variant: "error",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <div className="w-full max-w-md space-y-8">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold text-foreground">RAGLens</h1>
          <p className="text-sm text-muted-foreground">
            Chrome DevTools for RAG pipelines
          </p>
        </div>

        {/* Form */}
        <div className="rounded-lg border border-border bg-card p-8 shadow-sm space-y-6">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">
              Sign in to your account
            </h2>
            <p className="text-sm text-muted-foreground">
              Enter your email and password to continue
            </p>
          </div>

          {error && (
            <div className="rounded-md bg-red-500/10 border border-red-500/20 px-4 py-3 flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
              <p className="text-sm text-red-500">{error}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="email"
                autoFocus
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Enter your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="current-password"
              />
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                "Sign in"
              )}
            </Button>
          </form>

          <div className="text-center text-sm">
            <span className="text-muted-foreground">
              Don&apos;t have an account?{" "}
            </span>
            <Link
              href="/register"
              className="text-primary hover:text-primary/80 font-medium transition-colors"
            >
              Sign up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return <Suspense fallback={<div className="p-8 text-muted-foreground">Loading sign in…</div>}><LoginForm /></Suspense>;
}
