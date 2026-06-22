import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      // Test-only Worker config without the remote-only `ai` binding so the
      // suite runs offline (no Cloudflare credentials). See wrangler.test.jsonc.
      wrangler: { configPath: "./wrangler.test.jsonc" },
      miniflare: {
        compatibilityFlags: ["nodejs_compat"],
      },
    }),
  ],
  test: {
    server: {
      deps: {
        inline: ["ajv", "ajv-formats"],
      },
    },
  },
});
