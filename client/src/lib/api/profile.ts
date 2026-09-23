import type { Profile } from "@/types/profile";
import { apiFetch } from "./http";

export function getProfile(): Promise<Profile> {
  return apiFetch<Profile>("/me");
}

export function updateProfile(firstName: string, lastName: string): Promise<Profile> {
  return apiFetch<Profile>("/me", {
    method: "PATCH",
    body: JSON.stringify({ first_name: firstName, last_name: lastName }),
  });
}

export function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  return apiFetch<void>("/me/change-password", {
    method: "POST",
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    // A wrong current password also answers 401, but it means "that value was wrong," not "your
    // session died" - the default redirect-to-login behavior would otherwise fire on every wrong
    // attempt and silently bounce the user away instead of showing the error (see login() for the
    // same reasoning).
    redirectOnUnauthorized: false,
  });
}
