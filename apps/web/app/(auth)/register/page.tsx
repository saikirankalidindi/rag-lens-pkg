"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { AlertCircle, Loader2 } from "lucide-react";
import { authApi } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/ui/toast";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function RegisterPage() {
  const router = useRouter();
  const { login, isAuthenticated } = useAuth();
  const { toast } = useToast();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      router.push("/projects");
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Validation
    if (password.length < 8) {
      const message = "Password must be at least 8 characters";
      setError(message);
      toast({
        title: "Validation error",
        description: message,
        variant: "warning",
      });
      return;
    }

    if (password !== confirmPassword) {
      const message = "Passwords do not match";
      setError(message);
      toast({
        title: "Validation error",
        description: message,
        variant: "warning",
      });
      return;
    }

    setIsLoading(true);

    try {
      const response = await authApi.register({
        email,
        password,
        full_name: fullName || undefined,
      });

      // Use auth context to handle login
      await login(response.access_token);

      toast({
        title: "Account created!",
        description: "Welcome to RAGLens. Your account has been created successfully.",
        variant: "success",
      });

      // Redirect to projects
      router.push("/projects");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Registration failed";
      setError(message);
      toast({
        title: "Registration failed",
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
              Create your account
            </h2>
            <p className="text-sm text-muted-foreground">
              Get started with RAGLens for free
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
              <Label htmlFor="fullName">Full Name (optional)</Label>
              <Input
                id="fullName"
                type="text"
                placeholder="John Doe"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                disabled={isLoading}
                autoComplete="name"
                autoFocus
              />
            </div>

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
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="At least 8 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="new-password"
              />
              {password && password.length < 8 && (
                <p className="text-xs text-amber-500">
                  Password must be at least 8 characters
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password</Label>
              <Input
                id="confirmPassword"
                type="password"
                placeholder="Re-enter your password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="new-password"
              />
              {confirmPassword && password !== confirmPassword && (
                <p className="text-xs text-amber-500">
                  Passwords do not match
                </p>
              )}
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                "Create account"
              )}
            </Button>
          </form>

          <div className="text-center text-sm">
            <span className="text-muted-foreground">
              Already have an account?{" "}
            </span>
            <Link
              href="/login"
              className="text-primary hover:text-primary/80 font-medium transition-colors"
            >
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
