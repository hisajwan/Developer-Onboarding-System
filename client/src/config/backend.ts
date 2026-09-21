// Server-side only: the browser never sees this. It reaches the backend through the /api/backend proxy.
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";
