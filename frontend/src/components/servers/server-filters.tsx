import React, { useMemo } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Search, RefreshCw, Filter } from "@/lib/icons";
import type { ServerWithStatus } from "@/types";

interface ServerFiltersProps {
  searchTerm: string;
  onSearchChange: (value: string) => void;
  statusFilter: string;
  onStatusFilterChange: (value: string) => void;
  typeFilter: string;
  onTypeFilterChange: (value: string) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
  servers: ServerWithStatus[];
}

export const ServerFilters = React.memo(function ServerFilters({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusFilterChange,
  typeFilter,
  onTypeFilterChange,
  onRefresh,
  isRefreshing,
  servers,
}: ServerFiltersProps) {
  const serverTypes = useMemo(() => {
    const types = new Set(
      servers.map((s) => s.config?.transport?.type).filter(Boolean)
    );
    return Array.from(types);
  }, [servers]);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Filter className="h-5 w-5" />
          Filters
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col gap-4 md:flex-row">
          <div className="flex-1">
            <div className="relative">
              <Search className="text-muted-foreground absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2" />
              <Input
                placeholder="Search servers..."
                value={searchTerm}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-10"
                aria-label="Search servers"
                type="search"
              />
            </div>
          </div>

          <Select
            value={statusFilter}
            onChange={(e) => onStatusFilterChange(e.target.value)}
            className="w-full md:w-40"
            aria-label="Filter by status"
          >
            <option value="all">All Status</option>
            <option value="running">Running</option>
            <option value="stopped">Stopped</option>
            <option value="error">Error</option>
          </Select>

          <Select
            value={typeFilter}
            onChange={(e) => onTypeFilterChange(e.target.value)}
            className="w-full md:w-40"
            aria-label="Filter by type"
          >
            <option value="all">All Types</option>
            {serverTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </Select>

          <Button
            variant="outline"
            onClick={onRefresh}
            disabled={isRefreshing}
            className="w-full md:w-auto"
            aria-label={isRefreshing ? "Refreshing servers" : "Refresh servers"}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
        </div>
      </CardContent>
    </Card>
  );
});
