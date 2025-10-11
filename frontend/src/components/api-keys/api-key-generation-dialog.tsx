"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  useGenericMutation,
  commonMutations,
} from "@/hooks/use-generic-mutations";
import { Loader2, Plus, Key, CheckCircle } from "lucide-react";
import { CopyButton } from "@/components/common/copy-button";
import { toast } from "react-hot-toast";
import type { ApiKeyCreatedResponse } from "@/lib/api";

interface ApiKeyGenerationDialogProps {
  onSuccess: (apiKey: ApiKeyCreatedResponse) => void;
  children: React.ReactNode;
  open?: boolean;
  onOpenChange?: (open: boolean) => void;
}

export function ApiKeyGenerationDialog({
  onSuccess,
  children,
  open: controlledOpen,
  onOpenChange,
}: ApiKeyGenerationDialogProps) {
  const [internalOpen, setInternalOpen] = useState(false);
  const open = controlledOpen !== undefined ? controlledOpen : internalOpen;
  const setOpen = onOpenChange || setInternalOpen;
  const [step, setStep] = useState<"config" | "success">("config");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [createdKey, setCreatedKey] = useState<ApiKeyCreatedResponse | null>(
    null
  );

  const createApiKeyMutation = useGenericMutation({
    ...commonMutations.createApiKey,
    onSuccess: (result) => {
      setCreatedKey(result);
      setStep("success");
      onSuccess(result);
    },
  });

  const handleSubmit = () => {
    if (!name.trim()) {
      toast.error("Please provide a name for the API key");
      return;
    }

    createApiKeyMutation.mutate({
      name: name.trim(),
      description: description.trim() || undefined,
    });
  };

  const handleReset = () => {
    setName("");
    setDescription("");
    setCreatedKey(null);
    setStep("config");
    setOpen(false);
  };

  return (
    <>
      <div onClick={() => setOpen(true)}>{children}</div>

      <Dialog
        open={open}
        onOpenChange={(newOpen) => {
          if (onOpenChange) {
            onOpenChange(newOpen);
          } else {
            setInternalOpen(newOpen);
          }
        }}
      >
        <DialogContent className="max-w-2xl">
          {step === "config" ? (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2">
                  <Key className="h-5 w-5" />
                  <span>Create New API Key</span>
                </DialogTitle>
                <DialogDescription>
                  Generate a new API key for accessing MCP server endpoints
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-6 py-4">
                {/* Key Name */}
                <div className="space-y-2">
                  <Label htmlFor="name">Key Name</Label>
                  <Input
                    id="name"
                    placeholder="e.g., Production Server Key"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    maxLength={100}
                  />
                  <p className="text-muted-foreground text-sm">
                    A descriptive name for this key
                  </p>
                </div>

                {/* Description */}
                <div className="space-y-2">
                  <Label htmlFor="description">Description (Optional)</Label>
                  <Textarea
                    id="description"
                    placeholder="Describe what this key will be used for..."
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    rows={2}
                    maxLength={500}
                  />
                </div>
              </div>

              <DialogFooter>
                <Button
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    setOpen(false);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  onClick={handleSubmit}
                  disabled={!name.trim() || createApiKeyMutation.isPending}
                >
                  {createApiKeyMutation.isPending ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Plus className="mr-2 h-4 w-4" />
                  )}
                  {createApiKeyMutation.isPending
                    ? "Creating..."
                    : "Create Key"}
                </Button>
              </DialogFooter>
            </>
          ) : (
            <>
              <DialogHeader>
                <DialogTitle className="flex items-center space-x-2 text-green-600">
                  <CheckCircle className="h-5 w-5" />
                  <span>API Key Created</span>
                </DialogTitle>
                <DialogDescription>
                  Your new API key has been generated.
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label>API Key</Label>
                  <div className="flex items-center space-x-2">
                    <code className="bg-muted flex-1 rounded px-3 py-2 font-mono text-sm break-all">
                      {createdKey?.api_key || "Key not available"}
                    </code>
                    <CopyButton
                      text={createdKey?.api_key || ""}
                      size="sm"
                      variant="outline"
                      disabled={!createdKey?.api_key}
                    />
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button onClick={handleReset}>Done</Button>
              </DialogFooter>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
