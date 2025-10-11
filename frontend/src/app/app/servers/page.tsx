"use client";

import React, { useState, useMemo, useCallback } from "react";
import dynamic from "next/dynamic";
import { MainLayout } from "@/components/layout/main-layout";
import { ConfirmationDialog } from "@/components/common/confirmation-dialog";
import { Button } from "@/components/ui/button";
import { RequireAuth } from "@/components/auth/require-auth";
import { ServerFilters } from "@/components/servers/server-filters";
import { ServerGrid } from "@/components/servers/server-grid";
import {
  useServers,
  useStartServer,
  useStopServer,
} from "@/hooks/use-api-queries";
import {
  useGenericMutation,
  commonMutations,
} from "@/hooks/use-generic-mutations";
import type { ServerWithStatus, ServerConfig } from "@/types";
import { Plus } from "@/lib/icons";
import { LoadingCard } from "@/components/common/loading-spinner";

const ServerConfigDialog = dynamic(
  () =>
    import("@/components/servers/server-config-dialog").then((mod) => ({
      default: mod.ServerConfigDialog,
    })),
  {
    loading: () => <LoadingCard />,
  }
);

export default function ServersPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [showConfigDialog, setShowConfigDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [serverToDelete, setServerToDelete] = useState<string | null>(null);
  const [editingServer, setEditingServer] = useState<ServerWithStatus | null>(
    null
  );

  const {
    data: servers = [],
    isLoading,
    isError,
    error,
    refetch,
  } = useServers();
  const createServer = useGenericMutation(commonMutations.createServer);
  const updateServer = useGenericMutation(commonMutations.updateServer);
  const deleteServer = useGenericMutation(commonMutations.deleteServer);
  const startServer = useStartServer();
  const stopServer = useStopServer();

  const filteredServers = useMemo(
    () =>
      servers.filter((server) => {
        const matchesSearch = server.name
          .toLowerCase()
          .includes(searchTerm.toLowerCase());
        const matchesStatus =
          statusFilter === "all" || server.status?.state === statusFilter;
        const matchesType =
          typeFilter === "all" || server.config.transport.type === typeFilter;

        return matchesSearch && matchesStatus && matchesType;
      }),
    [servers, searchTerm, statusFilter, typeFilter]
  );

  const handleAddServer = useCallback(() => {
    setEditingServer(null);
    setShowConfigDialog(true);
  }, []);

  const handleEditServer = useCallback((server: ServerWithStatus) => {
    setEditingServer(server);
    setShowConfigDialog(true);
  }, []);

  const handleSaveServer = useCallback(
    async (name: string, config: ServerConfig) => {
      if (editingServer) {
        await updateServer.mutateAsync({ name, config });
      } else {
        await createServer.mutateAsync({ name, config });
      }
      setShowConfigDialog(false);
      setEditingServer(null);
    },
    [editingServer, createServer, updateServer]
  );

  const handleDeleteServer = useCallback((serverName: string) => {
    setServerToDelete(serverName);
    setShowDeleteDialog(true);
  }, []);

  const confirmDeleteServer = useCallback(async () => {
    if (serverToDelete) {
      const server = servers.find((s) => s.name === serverToDelete);
      if (server?.status?.state === "running") {
        await stopServer.mutateAsync(serverToDelete);
      }
      await deleteServer.mutateAsync(serverToDelete);
      setShowDeleteDialog(false);
      setServerToDelete(null);
    }
  }, [serverToDelete, servers, stopServer, deleteServer]);

  const handleStartServer = useCallback(
    (name: string) => {
      startServer.mutate({ name, request: {} });
    },
    [startServer]
  );

  const handleStopServer = useCallback(
    (name: string) => {
      stopServer.mutate(name);
    },
    [stopServer]
  );

  if (isLoading) {
    return (
      <MainLayout>
        <LoadingCard
          title="Loading Servers"
          description="Fetching server data, please wait..."
        />
      </MainLayout>
    );
  }

  if (isError) {
    return (
      <MainLayout>
        <div className="flex min-h-[400px] items-center justify-center">
          <div className="max-w-md text-center">
            <div className="text-destructive mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100">
              ⚠️
            </div>
            <h3 className="mb-2 text-lg font-semibold">
              Error Loading Servers
            </h3>
            <p className="text-muted-foreground mb-4">
              {error?.message || "Unknown error"}
            </p>
            <Button onClick={() => refetch()}>Try Again</Button>
          </div>
        </div>
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
              <h1 className="text-3xl font-bold">Servers</h1>
              <p className="text-muted-foreground mt-2">
                Manage and monitor your MCP servers
              </p>
            </div>
            <Button onClick={handleAddServer}>
              <Plus className="mr-2 h-4 w-4" />
              Add Server
            </Button>
          </div>

          {/* Filters */}
          <ServerFilters
            searchTerm={searchTerm}
            onSearchChange={setSearchTerm}
            statusFilter={statusFilter}
            onStatusFilterChange={setStatusFilter}
            typeFilter={typeFilter}
            onTypeFilterChange={setTypeFilter}
            onRefresh={() => refetch()}
            isRefreshing={isLoading}
            servers={servers}
          />

          {/* Server Grid */}
          <ServerGrid
            servers={filteredServers}
            onStartServer={handleStartServer}
            onStopServer={handleStopServer}
            onConfigureServer={handleEditServer}
            onDeleteServer={handleDeleteServer}
            isStarting={startServer.isPending}
            isStopping={stopServer.isPending}
            isLoading={isLoading}
          />

          {/* Dialogs */}
          {showConfigDialog && (
            <ServerConfigDialog
              open={showConfigDialog}
              onOpenChange={setShowConfigDialog}
              onSave={handleSaveServer}
              initialData={
                editingServer
                  ? {
                      name: editingServer.name,
                      config: editingServer.config,
                    }
                  : undefined
              }
            />
          )}

          {showDeleteDialog && (
            <ConfirmationDialog
              open={showDeleteDialog}
              onOpenChange={setShowDeleteDialog}
              onConfirm={confirmDeleteServer}
              title="Delete Server"
              description={`Are you sure you want to delete "${serverToDelete}"? This action cannot be undone.`}
              confirmText="Delete"
              cancelText="Cancel"
            />
          )}
        </div>
      </MainLayout>
    </RequireAuth>
  );
}
