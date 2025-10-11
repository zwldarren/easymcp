"use client";

import { z } from "zod";

// Common validation schemas for forms
export const commonSchemas = {
  // Server configuration
  serverName: z
    .string()
    .min(1, "Server name is required")
    .max(50, "Server name must be 50 characters or less")
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      "Server name can only contain letters, numbers, hyphens, and underscores"
    ),

  // API Key
  apiKeyName: z
    .string()
    .min(1, "Key name is required")
    .max(100, "Key name must be 100 characters or less"),

  apiKeyDescription: z
    .string()
    .max(500, "Description must be 500 characters or less")
    .optional(),

  // URL validation
  url: z
    .url("Please enter a valid URL")
    .max(500, "URL must be 500 characters or less"),

  // Timeout
  timeout: z
    .number()
    .min(1, "Timeout must be at least 1 second")
    .max(300, "Timeout must be 300 seconds or less"),

  // Environment variables
  envVarName: z
    .string()
    .min(1, "Variable name is required")
    .max(100, "Variable name must be 100 characters or less")
    .regex(
      /^[A-Z_][A-Z0-9_]*$/,
      "Variable name must start with a letter and contain only uppercase letters, numbers, and underscores"
    ),

  envVarValue: z
    .string()
    .max(1000, "Variable value must be 1000 characters or less"),

  // Headers
  headerName: z
    .string()
    .min(1, "Header name is required")
    .max(100, "Header name must be 100 characters or less")
    .regex(
      /^[A-Za-z0-9\-_]+$/,
      "Header name can only contain letters, numbers, hyphens, and underscores"
    ),

  headerValue: z
    .string()
    .max(500, "Header value must be 500 characters or less"),

  // Authentication
  username: z
    .string()
    .min(1, "Username is required")
    .max(50, "Username must be 50 characters or less")
    .regex(
      /^[a-zA-Z0-9_-]+$/,
      "Username can only contain letters, numbers, hyphens, and underscores"
    ),

  password: z
    .string()
    .min(1, "Password is required")
    .max(100, "Password must be 100 characters or less"),

  // Numeric ranges
  port: z
    .number()
    .min(1, "Port must be at least 1")
    .max(65535, "Port must be 65535 or less"),

  days: z
    .number()
    .min(0, "Days must be 0 or more")
    .max(365, "Days must be 365 or less"),
};

// Form field configurations
export const formFieldConfigs = {
  serverName: {
    label: "Server Name",
    placeholder: "my-server",
    description: "A unique name for your MCP server",
  },
  apiKeyName: {
    label: "Key Name",
    placeholder: "e.g., Production Server Key",
    description: "A descriptive name for this API key",
  },
  apiKeyDescription: {
    label: "Description (Optional)",
    placeholder: "Describe what this key will be used for...",
  },
  url: {
    label: "URL",
    placeholder: "https://api.example.com/mcp",
    description: "The endpoint URL for your MCP server",
  },
  timeout: {
    label: "Timeout (seconds)",
    placeholder: "60",
    description: "Maximum time to wait for server responses",
  },
  envVarName: {
    label: "Variable Name",
    placeholder: "API_KEY",
  },
  envVarValue: {
    label: "Value",
    placeholder: "your-api-key-here",
  },
  headerName: {
    label: "Header Name",
    placeholder: "Authorization",
  },
  headerValue: {
    label: "Header Value",
    placeholder: "Bearer your-token-here",
  },
};

// Helper function to create form field schemas
export function createFormFieldSchema(
  fieldName: keyof typeof commonSchemas,
  required = true
) {
  const schema = commonSchemas[fieldName];
  return required ? schema : schema.optional();
}

// Helper to get form field configuration
export function getFormFieldConfig(fieldName: keyof typeof formFieldConfigs) {
  return formFieldConfigs[fieldName];
}
