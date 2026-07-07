/**
 * Configuration helpers for CloudBoard production.
 *
 * Vite replaces `import.meta.env.VITE_...` at build time with values from the
 * environment. This module provides a single source of truth for retrieving the
 * Gemini API key and any future env‑variables.
 */

/**
 * Returns the Gemini API key if it is provided via an environment variable.
 * Falls back to the value stored in `localStorage` (used during development).
 */
export function getGeminiApiKey() {
  // Vite injects env vars prefixed with VITE_ at build time.
  // eslint-disable-next-line no-undef
  const envKey = typeof import !== "undefined" && import.meta && import.meta.env && import.meta.env.VITE_GEMINI_API_KEY;
  if (envKey) {
    return envKey;
  }
  // Development fallback – stored in localStorage via SettingsRBAC.
  return localStorage.getItem("CLOUDBOARD_GEMINI_KEY") || "";
}

/**
 * Helper to determine if we are running a production build.
 */
export const isProduction = () => {
  // Vite sets `import.meta.env.PROD` to true in production mode.
  return typeof import !== "undefined" && import.meta && import.meta.env && import.meta.env.PROD;
};
