
// Load .env file for local development. In production (Railway/Docker),
// environment variables are injected by the platform.
try { require("dotenv/config"); } catch (_) {}

import { defineConfig, env } from "prisma/config";

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  engine: "classic",
  datasource: {
    url: env("DATABASE_URL"),
  },
});
