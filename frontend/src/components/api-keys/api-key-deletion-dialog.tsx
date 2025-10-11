"use client";

import { ConfirmationDialog } from "@/components/common/confirmation-dialog";
import type { ApiKeyResponse } from "@/lib/api";

interface ApiKeyDeletionDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onDelete: () => void;
  apiKey: ApiKeyResponse | null;
  isLoading?: boolean;
}

export function ApiKeyDeletionDialog({
  open,
  onOpenChange,
  onDelete,
  apiKey,
  isLoading = false,
}: ApiKeyDeletionDialogProps) {
  return (
    <ConfirmationDialog
      open={open}
      onOpenChange={onOpenChange}
      onConfirm={onDelete}
      title="Delete API Key"
      description={
        apiKey
          ? `Are you sure you want to permanently delete the API key "${apiKey.name}"?`
          : "Are you sure you want to delete this API key?"
      }
      confirmText="Delete Key"
      cancelText="Cancel"
      confirmVariant="destructive"
      isConfirming={isLoading}
    />
  );
}
