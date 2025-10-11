import { useMemo } from "react";

export function useCodeExamples(selectedServer: string) {
  const openAICurlExample = useMemo(
    () => `curl --location 'https://api.openai.com/v1/responses' \\
--header 'Content-Type: application/json' \\
--header "Authorization: Bearer $OPENAI_API_KEY" \\
--data '{
    "model": "gpt-5",
    "tools": [
        {
          "type": "mcp",
          "server_label": "easymcp",
          "server_url": "https://example.com/servers/${selectedServer || "{server_name}"}/mcp",
          "require_approval": "never",
          "headers": {
            "x-api-key": "YOUR_API_KEY"
          }
        }
    ],
    "input": "Run available tools",
    "tool_choice": "required"
}'`,
    [selectedServer]
  );

  const streamableHttpExample = useMemo(
    () => `{
  "mcpServers": {
    "${selectedServer || "your-server"}": {
      "transport": {
        "type": "streamable_http",
        "url": "https://example.com/servers/${selectedServer || "{server_name}"}/mcp",
        "headers": {
          "x-api-key": "YOUR_API_KEY"
        }
      }
    }
  }
}`,
    [selectedServer]
  );

  return {
    openAICurlExample,
    streamableHttpExample,
  };
}
