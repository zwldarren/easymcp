import { z } from "zod";

const envSchema = z.object({
  NEXT_PUBLIC_API_URL: z
    .url("Invalid API URL")
    .default("http://localhost:8000"),
  NODE_ENV: z
    .enum(["development", "production", "test"])
    .default("development"),
});

export function validateEnv() {
  try {
    const env = envSchema.parse(process.env);
    return env;
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error("Environment validation failed:", error.issues);
      throw new Error("Invalid environment configuration");
    }
    throw error;
  }
}

export const env = validateEnv();
