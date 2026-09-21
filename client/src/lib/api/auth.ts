import type { Session } from "@/types/auth";
import { apiFetch } from "./http";

export function login(username: string, password: string): Promise<Session> {
  return apiFetch<Session>("/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    redirectOnUnauthorized: false,
  });
}

export function logout(): Promise<void> {
  return apiFetch<void>("/logout", { method: "POST" });
}
