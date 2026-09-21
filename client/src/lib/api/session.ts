import { cookies } from "next/headers";
import { BACKEND_URL } from "@/config/backend";
import { SESSION_COOKIE } from "@/config/session";
import type { Session } from "@/types/auth";

/**
 * Server-side only (Server Components): asks the backend whether the visitor's session cookie is
 * valid. Returns null when there is no cookie, it is invalid or expired, or the backend is down.
 */
export async function getSession(): Promise<Session | null> {
  const token = (await cookies()).get(SESSION_COOKIE)?.value;
  if (!token) return null;
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/session`, {
      headers: { Cookie: `${SESSION_COOKIE}=${token}` },
      cache: "no-store",
    });
    return response.ok ? ((await response.json()) as Session) : null;
  } catch {
    return null;
  }
}
