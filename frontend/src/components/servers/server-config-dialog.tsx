"use client";

import { useState, useEffect, useCallback } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Select } from "@/components/ui/select";
import { ServerConfig } from "@/lib/api";
import { Plus, X } from "lucide-react";

const stdioConfigSchema = z.object({
  type: z.literal("stdio"),
  command: z.string().min(1, "Command is required"),
  args: z.array(z.string()),
  env: z.record(z.string(), z.string()),
});

const sseConfigSchema = z.object({
  type: z.literal("sse"),
  url: z.url("Invalid URL"),
  headers: z.record(z.string(), z.string()),
});

const streamableHttpConfigSchema = z.object({
  type: z.literal("streamable-http"),
  url: z.url("Invalid URL"),
  headers: z.record(z.string(), z.string()),
});

const transportConfigSchema = z.discriminatedUnion("type", [
  stdioConfigSchema,
  sseConfigSchema,
  streamableHttpConfigSchema,
]);

const serverConfigSchema = z.object({
  serverName: z.string().min(1, "Server name is required"),
  transport: transportConfigSchema,
  enabled: z.boolean(),
  timeout: z.number(),
});

interface ServerConfigDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSave: (name: string, config: ServerConfig) => void;
  initialData?: {
    name: string;
    config: ServerConfig;
  };
}

export function ServerConfigDialog({
  open,
  onOpenChange,
  onSave,
  initialData,
}: ServerConfigDialogProps) {
  const [envKey, setEnvKey] = useState("");
  const [envValue, setEnvValue] = useState("");
  const [headerKey, setHeaderKey] = useState("");
  const [headerValue, setHeaderValue] = useState("");

  const getDefaultValues = useCallback(
    () => ({
      serverName: initialData?.name || "",
      transport: initialData?.config.transport || {
        type: "stdio" as const,
        command: "",
        args: [],
        env: {},
      },
      enabled: initialData?.config.enabled ?? true,
      timeout: initialData?.config.timeout ?? 60,
    }),
    [initialData]
  );

  const form = useForm<z.infer<typeof serverConfigSchema>>({
    resolver: zodResolver(serverConfigSchema),
    defaultValues: getDefaultValues(),
  });

  useEffect(() => {
    if (open) {
      form.reset(getDefaultValues());
    }
  }, [open, initialData, form, getDefaultValues]);

  const transportType = form.watch("transport.type");

  const addEnvVar = () => {
    if (envKey && envValue) {
      const currentEnv =
        form.getValues("transport.type") === "stdio"
          ? form.getValues("transport.env")
          : {};
      form.setValue(
        "transport.env",
        { ...currentEnv, [envKey]: envValue },
        { shouldValidate: true, shouldDirty: true }
      );
      setEnvKey("");
      setEnvValue("");
    }
  };

  const removeEnvVar = (key: string) => {
    const currentEnv = form.getValues("transport.env") || {};
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { [key]: _, ...rest } = currentEnv;
    form.setValue("transport.env", rest, {
      shouldValidate: true,
      shouldDirty: true,
    });
  };

  const addHeader = () => {
    if (headerKey && headerValue) {
      const currentHeaders = form.getValues("transport.headers") || {};
      form.setValue(
        "transport.headers",
        {
          ...currentHeaders,
          [headerKey]: headerValue,
        },
        { shouldValidate: true, shouldDirty: true }
      );
      setHeaderKey("");
      setHeaderValue("");
    }
  };

  const removeHeader = (key: string) => {
    const currentHeaders = form.getValues("transport.headers") || {};
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { [key]: _, ...rest } = currentHeaders;
    form.setValue("transport.headers", rest, {
      shouldValidate: true,
      shouldDirty: true,
    });
  };

  const onSubmit = (values: z.infer<typeof serverConfigSchema>) => {
    const serverName = values.serverName.trim();
    if (!serverName) {
      form.setError("serverName", { message: "Server name is required" });
      return;
    }

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    const { serverName: _ignored, ...config } = values;

    const originalName = initialData?.name;
    onSave(originalName || serverName, config);
    onOpenChange(false);
    form.reset(getDefaultValues());
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {initialData ? "Edit Server" : "Add New Server"}
          </DialogTitle>
          <DialogDescription>
            Configure your MCP server settings
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <div className="space-y-4">
              <FormField
                control={form.control}
                name="serverName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Server Name</FormLabel>
                    <FormControl>
                      <Input placeholder="my-server" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="transport.type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Transport Type</FormLabel>
                    <FormControl>
                      <Select {...field}>
                        <option value="stdio">stdio</option>
                        <option value="sse">SSE</option>
                        <option value="streamable-http">Streamable HTTP</option>
                      </Select>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              {transportType === "stdio" && (
                <>
                  <FormField
                    control={form.control}
                    name="transport.command"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Command</FormLabel>
                        <FormControl>
                          <Input placeholder="python" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />

                  <FormField
                    control={form.control}
                    name="transport.args"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Arguments</FormLabel>
                        <FormControl>
                          <Textarea
                            placeholder="server.py&#10;--port=8000"
                            {...field}
                            onChange={(e) =>
                              field.onChange(e.target.value.split("\n"))
                            }
                            value={
                              Array.isArray(field.value)
                                ? field.value.join("\n")
                                : ""
                            }
                          />
                        </FormControl>
                        <FormDescription>One argument per line</FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </>
              )}

              {(transportType === "sse" ||
                transportType === "streamable-http") && (
                <FormField
                  control={form.control}
                  name="transport.url"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>URL</FormLabel>
                      <FormControl>
                        <Input
                          placeholder={`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/mcp`}
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              )}

              {transportType !== "stdio" && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium">Headers</Label>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Header name"
                      value={headerKey}
                      onChange={(e) => setHeaderKey(e.target.value)}
                      className="flex-1"
                    />
                    <Input
                      placeholder="Header value"
                      value={headerValue}
                      onChange={(e) => setHeaderValue(e.target.value)}
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      onClick={addHeader}
                      size="sm"
                      className="flex-shrink-0"
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(
                      form.getValues("transport.headers") || {}
                    ).map(([key, value]) => (
                      <Badge
                        key={key}
                        variant="secondary"
                        className="flex items-center gap-1 px-2 py-1"
                      >
                        {key}: {value}
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="hover:bg-destructive/20 h-auto w-auto p-0.5"
                          onClick={() => removeHeader(key)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {transportType === "stdio" && (
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Environment Variables
                  </Label>
                  <div className="flex space-x-2">
                    <Input
                      placeholder="Variable name"
                      value={envKey}
                      onChange={(e) => setEnvKey(e.target.value)}
                      className="flex-1"
                    />
                    <Input
                      placeholder="Value"
                      value={envValue}
                      onChange={(e) => setEnvValue(e.target.value)}
                      className="flex-1"
                    />
                    <Button
                      type="button"
                      onClick={addEnvVar}
                      size="sm"
                      className="flex-shrink-0"
                    >
                      <Plus className="h-4 w-4" />
                    </Button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(form.getValues("transport.env") || {}).map(
                      ([key, value]) => (
                        <Badge
                          key={key}
                          variant="secondary"
                          className="flex items-center gap-1 px-2 py-1"
                        >
                          {key}={value}
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            className="hover:bg-destructive/20 h-auto w-auto p-0.5"
                            onClick={() => removeEnvVar(key)}
                          >
                            <X className="h-3 w-3" />
                          </Button>
                        </Badge>
                      )
                    )}
                  </div>
                </div>
              )}

              <FormField
                control={form.control}
                name="timeout"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Timeout (seconds)</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        min="1"
                        max="300"
                        {...field}
                        onChange={(e) =>
                          field.onChange(parseInt(e.target.value))
                        }
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit">
                {initialData ? "Update" : "Create"} Server
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
}
