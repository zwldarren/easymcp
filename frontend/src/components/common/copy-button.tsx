"use client";

import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Copy, Check } from "@/lib/icons";
import { cn } from "@/lib/utils";
import { memo } from "react";

interface CopyButtonProps {
  text: string;
  className?: string;
  size?: "sm" | "default" | "lg" | "icon";
  variant?:
    | "default"
    | "destructive"
    | "outline"
    | "secondary"
    | "ghost"
    | "link";
  onSuccess?: () => void;
  onError?: (error: Error) => void;
  showToast?: boolean;
  disabled?: boolean;
}

export const CopyButton = memo(function CopyButton({
  text,
  className,
  size = "icon",
  variant = "ghost",
  onSuccess,
  onError,
  showToast = true,
  disabled = false,
}: CopyButtonProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      onSuccess?.();

      if (showToast) {
        const toast = await import("react-hot-toast").then((m) => m.toast);
        toast.success("Copied to clipboard!");
      }

      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      const error = err instanceof Error ? err : new Error("Failed to copy");
      onError?.(error);

      if (showToast) {
        const toast = await import("react-hot-toast").then((m) => m.toast);
        toast.error("Failed to copy. Please copy manually.");
      }
    }
  }, [text, onSuccess, onError, showToast]);

  return (
    <Button
      variant={variant}
      size={size}
      className={cn("transition-all duration-200", className)}
      onClick={handleCopy}
      title={copied ? "Copied!" : "Copy to clipboard"}
      disabled={disabled || copied}
    >
      {copied ? (
        <Check className="h-4 w-4 text-green-600" />
      ) : (
        <Copy className="h-4 w-4" />
      )}
    </Button>
  );
});
