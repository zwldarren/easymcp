"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { MainLayout } from "@/components/layout/main-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { LoadingState, EmptyState } from "@/components/common/state-components";
import { RequireAuth } from "@/components/auth/require-auth";
import { ApiKeyListItem } from "@/components/api-keys/api-key-list-item";
import { useApiKeys, useDeleteApiKey } from "@/hooks/use-api-queries";
import { Plus, Key, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import type { ApiKeyResponse } from "@/lib/api";

const ApiKeyGenerationDialog = dynamic(
  () =>
    import("@/components/api-keys/api-key-generation-dialog").then((mod) => ({
      default: mod.ApiKeyGenerationDialog,
    })),
  {
    loading: () => <div>Loading...</div>,
  }
);

const ApiKeyDeletionDialog = dynamic(
  () =>
    import("@/components/api-keys/api-key-deletion-dialog").then((mod) => ({
      default: mod.ApiKeyDeletionDialog,
    })),
  {
    loading: () => <div>Loading...</div>,
  }
);

export default function ApiKeysPage() {
  const { data: apiKeysData, isLoading, refetch } = useApiKeys();
  const apiKeys = Array.isArray(apiKeysData)
    ? apiKeysData
    : apiKeysData?.api_keys || [];
  const [searchQuery, setSearchQuery] = useState("");
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [keyToDelete, setKeyToDelete] = useState<ApiKeyResponse | null>(null);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  // Use delete API key mutation
  const deleteApiKeyMutation = useDeleteApiKey();

  // Filter API keys by search
  const filteredKeys = apiKeys.filter((key) => {
    const matchesSearch =
      key.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      key.key_prefix.toLowerCase().includes(searchQuery.toLowerCase());

    return matchesSearch;
  });

  const handleDeleteKey = (keyId: number) => {
    const key = apiKeys.find((k) => k.id === keyId);
    if (key) {
      setKeyToDelete(key);
      setDeleteDialogOpen(true);
    }
  };

  const handleKeyCreated = () => {
    refetch();
  };

  const handleDeleteConfirm = () => {
    if (keyToDelete) {
      deleteApiKeyMutation.mutate(keyToDelete.id, {
        onSuccess: () => {
          setDeleteDialogOpen(false);
          setKeyToDelete(null);
        },
      });
    }
  };

  // Handle loading and error states
  if (isLoading) {
    return (
      <MainLayout>
        <LoadingState title="Loading API keys..." />
      </MainLayout>
    );
  }

  return (
    <RequireAuth>
      <MainLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">API Keys</h1>
              <p className="text-muted-foreground mt-2">
                Manage your API keys for accessing MCP server endpoints
              </p>
            </div>
            <Button onClick={() => setCreateDialogOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create New Key
            </Button>
          </div>

          <ApiKeyGenerationDialog
            onSuccess={handleKeyCreated}
            open={createDialogOpen}
            onOpenChange={setCreateDialogOpen}
          >
            <div />
          </ApiKeyGenerationDialog>

          {/* Search */}
          <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
            <div className="flex flex-1 items-center space-x-4">
              <div className="relative max-w-sm flex-1">
                <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 transform" />
                <Input
                  placeholder="Search keys by name or prefix..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
          </div>

          {/* API Keys List */}
          <div className="space-y-2">
            {filteredKeys.length > 0 ? (
              filteredKeys.map((apiKey) => (
                <ApiKeyListItem
                  key={apiKey.id}
                  apiKey={apiKey}
                  onDelete={handleDeleteKey}
                />
              ))
            ) : (
              <Card>
                <CardContent className="py-8">
                  <EmptyState
                    icon={Key}
                    title="No API keys found"
                    description={
                      searchQuery
                        ? "No keys match your search criteria"
                        : "Get started by creating your first API key"
                    }
                    action={
                      searchQuery
                        ? {
                            label: "Clear search",
                            onClick: () => {
                              setSearchQuery("");
                            },
                            variant: "outline",
                          }
                        : {
                            label: "Create First Key",
                            onClick: () => {
                              setCreateDialogOpen(true);
                            },
                          }
                    }
                  />
                </CardContent>
              </Card>
            )}
          </div>

          {/* Deletion Dialog */}
          <ApiKeyDeletionDialog
            open={deleteDialogOpen}
            onOpenChange={setDeleteDialogOpen}
            onDelete={handleDeleteConfirm}
            apiKey={keyToDelete}
            isLoading={deleteApiKeyMutation.isPending}
          />
        </div>
      </MainLayout>
    </RequireAuth>
  );
}
