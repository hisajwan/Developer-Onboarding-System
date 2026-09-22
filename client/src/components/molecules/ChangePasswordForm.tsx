"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { TextInput } from "@/components/atoms/TextInput";
import { ApiError } from "@/lib/api/http";
import { changePassword } from "@/lib/api/profile";

interface ChangePasswordFormProps {
  /** Called once the password has actually changed - the modal that hosts this form closes on it. */
  onSuccess: () => void;
}

// The button stays enabled and submit itself validates: a form that flips a submit button's own
// disabled state on and off as you type is easy to get subtly wrong (a stale value, a missed
// dependency) and gives no feedback about *what's* still missing - a submit attempt saying so
// plainly is both simpler and clearer.
export function ChangePasswordForm({ onSuccess }: ChangePasswordFormProps) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function validate(): string | null {
    if (!currentPassword) return "Enter your current password.";
    if (newPassword.length < 8) return "New password must be at least 8 characters.";
    if (newPassword !== confirmPassword) return "Passwords do not match.";
    return null;
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }
    setError(null);
    setIsSaving(true);
    try {
      await changePassword(currentPassword, newPassword);
      onSuccess();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not change your password.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1 text-xs font-medium">
        Current password
        <TextInput
          type="password"
          value={currentPassword}
          onChange={(event) => setCurrentPassword(event.target.value)}
          autoComplete="current-password"
          autoFocus
        />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        New password
        <TextInput
          type="password"
          value={newPassword}
          onChange={(event) => setNewPassword(event.target.value)}
          autoComplete="new-password"
        />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Confirm new password
        <TextInput
          type="password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          autoComplete="new-password"
        />
      </label>
      {error && (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
      <Button type="submit" disabled={isSaving}>
        {isSaving ? "Changing..." : "Change password"}
      </Button>
    </form>
  );
}
