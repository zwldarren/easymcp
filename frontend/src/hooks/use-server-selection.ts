import { useState, useEffect } from "react";
import { useServers } from "@/hooks/use-api-queries";

export function useServerSelection(defaultToFirst = true) {
  const { data: servers = [], isLoading } = useServers();
  const [selectedServer, setSelectedServer] = useState<string>("");

  // Set default server when servers are loaded
  useEffect(() => {
    if (defaultToFirst && servers.length > 0 && !selectedServer) {
      setSelectedServer(servers[0].name);
    }
  }, [servers, selectedServer, defaultToFirst]);

  return {
    selectedServer,
    setSelectedServer,
    servers,
    isLoading,
  };
}
