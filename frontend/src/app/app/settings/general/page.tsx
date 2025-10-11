"use client";

import { useState, useEffect } from "react";
import { MainLayout } from "@/components/layout/main-layout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Settings, Save, RefreshCw, Download } from "lucide-react";
import { useGlobalConfig, useServers } from "@/hooks/use-api-queries";
import {
  useGenericMutation,
  commonMutations,
} from "@/hooks/use-generic-mutations";
import type { GlobalConfig } from "@/lib/api";
import { LoadingCard } from "@/components/common/loading-spinner";
import { RequireAuth } from "@/components/auth/require-auth";

export default function ConfigPage() {
  const {
    data: globalConfigData,
    isLoading: isLoadingGlobal,
    refetch: refetchGlobal,
  } = useGlobalConfig();
  const { data: servers = [], isLoading: isLoadingServers } = useServers();
  const updateGlobalConfig = useGenericMutation(
    commonMutations.updateGlobalConfig
  );

  const [formState, setFormState] = useState<GlobalConfig | null>(null);

  useEffect(() => {
    if (globalConfigData) {
      setFormState(globalConfigData);
    }
  }, [globalConfigData]);

  const handleSave = () => {
    if (formState) {
      updateGlobalConfig.mutate(formState);
    }
  };

  const handleRefresh = () => {
    refetchGlobal();
  };

  const exportConfig = () => {
    const config = {
      global: formState,
      servers: servers.map((s) => ({ [s.name]: s.config })),
    };
    const blob = new Blob([JSON.stringify(config, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "easymcp-config.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const isLoading = isLoadingGlobal || isLoadingServers;

  if (isLoading || !formState) {
    return (
      <MainLayout>
        <LoadingCard title="Loading settings..." />
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
              <h1 className="text-3xl font-bold">General Settings</h1>
              <p className="text-muted-foreground mt-2">
                Manage global settings and server configurations
              </p>
            </div>
            <div className="flex space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={exportConfig}
                className="text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              >
                <Download className="mr-2 h-4 w-4" />
                Export
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
                className="text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              >
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
            </div>
          </div>

          {/* Global Configuration */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="mr-2 h-5 w-5" />
                Global Configuration
              </CardTitle>
              <CardDescription>
                System-wide settings that affect all MCP servers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Stateless Mode</Label>
                      <p className="text-muted-foreground text-sm">
                        Run without persistent state
                      </p>
                    </div>
                    <Switch
                      checked={formState.stateless}
                      onCheckedChange={(checked: boolean) =>
                        setFormState(
                          (prev) => prev && { ...prev, stateless: checked }
                        )
                      }
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Pass Environment</Label>
                      <p className="text-muted-foreground text-sm">
                        Pass environment variables to servers
                      </p>
                    </div>
                    <Switch
                      checked={formState.pass_environment}
                      onCheckedChange={(checked: boolean) =>
                        setFormState(
                          (prev) =>
                            prev && { ...prev, pass_environment: checked }
                        )
                      }
                    />
                  </div>
                </div>
              </div>

              <div className="flex justify-end">
                <Button
                  onClick={handleSave}
                  disabled={updateGlobalConfig.isPending}
                >
                  <Save className="mr-2 h-4 w-4" />
                  {updateGlobalConfig.isPending ? "Saving..." : "Save Changes"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Server Configuration */}
          <Card>
            <CardHeader>
              <CardTitle>Server Configuration</CardTitle>
              <CardDescription>
                MCP server configurations (manage servers from the Servers page)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="text-muted-foreground text-sm">
                  Total servers configured: {servers.length}
                </div>

                {servers.length > 0 ? (
                  <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {servers.map((server) => (
                      <div key={server.name} className="rounded-lg border p-4">
                        <div className="mb-2 flex items-center justify-between">
                          <h4 className="font-medium">{server.name}</h4>
                          <Badge variant="outline">
                            {server.config?.transport?.type || "Unknown"}
                          </Badge>
                        </div>
                        <div className="text-muted-foreground text-sm">
                          <div>Timeout: {server.config?.timeout || 0}s</div>
                          <div>
                            Enabled: {server.config?.enabled ? "Yes" : "No"}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-muted-foreground py-8 text-center">
                    No servers configured yet. Add servers from the Servers
                    page.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </MainLayout>
    </RequireAuth>
  );
}
