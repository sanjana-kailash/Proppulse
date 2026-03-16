// Central API base URL.
// In local dev (npm run dev) this is '' — Vite proxies /api/* to localhost:8000.
// In production this is your Render backend URL, injected by Vercel at build time
// via the VITE_API_URL environment variable.
export const API_BASE = import.meta.env.VITE_API_URL ?? ''
