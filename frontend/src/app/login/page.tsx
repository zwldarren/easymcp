"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LoginForm } from "@/components/auth/login-form";
import { useAuth } from "@/hooks/use-auth";
import { EasyMcpIcon } from "@/components/common/easymcp-icon";
import { cn } from "@/lib/utils";

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      router.push("/");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="bg-background flex min-h-screen items-center justify-center">
        <div className="flex items-center space-x-2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />
          <span>Loading...</span>
        </div>
      </div>
    );
  }

  if (isAuthenticated) {
    return null; // Will redirect to home page
  }

  const handleLoginSuccess = () => {
    router.push("/");
  };

  return (
    <div className="bg-background flex min-h-screen items-center justify-center p-4">
      <div className="w-full max-w-lg space-y-8">
        {/* Header */}
        <div className="text-center">
          <div className="mb-4 flex items-center justify-center">
            <div
              className={cn(
                "bg-primary/10 rounded-lg p-3",
                "flex items-center justify-center"
              )}
            >
              <EasyMcpIcon className="text-primary h-8 w-8" />
            </div>
          </div>
          <h1 className="text-3xl font-bold tracking-tight">EasyMCP</h1>
          <p className="text-muted-foreground mt-2">MCP Proxy Server</p>
        </div>

        {/* Login Form */}
        <LoginForm onSuccess={handleLoginSuccess} />

        {/* Footer */}
        <div className="text-center">
          <p className="text-muted-foreground text-sm">
            Single sign-on authentication system
          </p>
        </div>
      </div>
    </div>
  );
}
