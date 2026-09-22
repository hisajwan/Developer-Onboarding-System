import type { Session, SignupFields } from "@/types/auth";
import { apiFetch } from "./http";

export function login(username: string, password: string): Promise<Session> {
  return apiFetch<Session>("/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
    redirectOnUnauthorized: false,
  });
}

export function signup(fields: SignupFields): Promise<Session> {
  return apiFetch<Session>("/signup", {
    method: "POST",
    body: JSON.stringify(fields),
    redirectOnUnauthorized: false,
  });
}

export function logout(): Promise<void> {
  return apiFetch<void>("/logout", { method: "POST" });
}
