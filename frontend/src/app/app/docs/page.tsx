"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  MetricCard,
  StepList,
  ServerSelector,
  CodeExample,
  ParameterList,
} from "@/components";
import { Code, Terminal, Globe } from "lucide-react";
import { MainLayout } from "@/components/layout/main-layout";
import { useServerSelection } from "@/hooks/use-server-selection";
import { useCodeExamples } from "@/hooks/use-code-examples";

export default function DocumentationPage() {
  const { selectedServer, setSelectedServer } = useServerSelection();
  const { openAICurlExample, streamableHttpExample } =
    useCodeExamples(selectedServer);

  return (
    <MainLayout>
      <div className="mx-auto max-w-4xl space-y-8">
        {/* Header */}
        <div className="space-y-4">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Documentation</h1>
            <p className="text-muted-foreground mt-2 text-lg">
              Learn how to integrate EasyMCP with your applications using two
              different methods.
            </p>
          </div>
        </div>

        {/* Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Globe className="h-5 w-5" />
              <span>Overview</span>
            </CardTitle>
            <CardDescription>
              EasyMCP provides a proxy server that merges
              stdio/sse/streamableHttp MCP servers into a unified application.
              You can connect to it using either OpenAI&apos;s MCP integration
              or direct Streamable HTTP Transport.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <MetricCard
                title="OpenAI API Integration"
                value="Seamless"
                icon={Code}
                description="Use MCP tools directly through OpenAI's API with built-in tool orchestration."
              />
              <MetricCard
                title="Streamable HTTP Transport"
                value="Direct"
                icon={Terminal}
                description="Direct MCP connection using HTTP transport with custom configuration."
              />
            </div>
          </CardContent>
        </Card>

        {/* Usage Methods */}
        <Card>
          <CardHeader>
            <CardTitle>Usage Methods</CardTitle>
            <CardDescription>
              Choose the integration method that best fits your application
              requirements.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="openai" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger
                  value="openai"
                  className="flex items-center space-x-2"
                >
                  <Code className="h-4 w-4" />
                  <span>OpenAI API</span>
                </TabsTrigger>
                <TabsTrigger
                  value="streamable"
                  className="flex items-center space-x-2"
                >
                  <Terminal className="h-4 w-4" />
                  <span>Streamable HTTP</span>
                </TabsTrigger>
              </TabsList>

              <TabsContent value="openai" className="mt-6 space-y-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="mb-2 text-lg font-semibold">
                      OpenAI API Integration
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Use MCP tools directly through OpenAI&apos;s API. The
                      OpenAI platform will handle tool orchestration and
                      execution automatically.
                    </p>
                  </div>

                  <ServerSelector
                    selectedServer={selectedServer}
                    onServerChange={setSelectedServer}
                    id="server-select-openai"
                  />

                  <CodeExample
                    title="Example Request"
                    code={openAICurlExample}
                  />

                  <div className="mt-6">
                    <ParameterList
                      parameters={[
                        {
                          name: "server_url",
                          description: " Your EasyMCP server endpoint",
                        },
                        {
                          name: "server_label",
                          description: " Custom label for identification",
                        },
                        {
                          name: "require_approval",
                          description: " Auto-approval setting",
                        },
                        {
                          name: "headers",
                          description: " Authentication headers",
                        },
                      ]}
                    />
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="streamable" className="mt-6 space-y-6">
                <div className="space-y-4">
                  <div>
                    <h3 className="mb-2 text-lg font-semibold">
                      Streamable HTTP Transport
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Configure your MCP client to use the Streamable HTTP
                      transport with your server URL and authentication headers.
                    </p>
                  </div>

                  <ServerSelector
                    selectedServer={selectedServer}
                    onServerChange={setSelectedServer}
                    id="server-select-streamable"
                  />

                  <CodeExample
                    title="MCP Configuration"
                    code={streamableHttpExample}
                  />

                  <div className="mt-6">
                    <ParameterList
                      parameters={[
                        {
                          name: "url",
                          description: " Your MCP server endpoint",
                        },
                        {
                          name: "headers",
                          description: " Authentication and other headers",
                        },
                        {
                          name: "type",
                          description: " Transport type (streamable_http)",
                        },
                        {
                          name: "server_name",
                          description: " Dynamic server selection",
                        },
                      ]}
                    />
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Getting Started */}
        <Card>
          <CardHeader>
            <CardTitle>Getting Started</CardTitle>
            <CardDescription>
              Follow these steps to start using EasyMCP in your application.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <StepList
              steps={[
                {
                  title: "Set up your EasyMCP server",
                  description:
                    "Deploy and configure your EasyMCP proxy server with the necessary MCP servers.",
                },
                {
                  title: "Generate API keys",
                  description:
                    "Create secure API keys for authentication through the settings panel.",
                },
                {
                  title: "Choose integration method",
                  description:
                    "Select either OpenAI API integration or Streamable HTTP Transport based on your needs.",
                },
                {
                  title: "Integrate and test",
                  description:
                    "Implement the integration using the provided examples and test your setup.",
                },
              ]}
            />
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
}
