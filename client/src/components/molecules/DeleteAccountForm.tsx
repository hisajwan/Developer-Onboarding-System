"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { TextInput } from "@/components/atoms/TextInput";
import { ApiError } from "@/lib/api/http";

interface DeleteAccountFormProps {
  /** Deletes the account; the page leaves for /login once it resolves. */
  onSubmit: (password: string) => Promise<void>;
  onCancel: () => void;
}

/** Asks for the password once more before the account and everything in it is deleted. */
export function DeleteAccountForm({ onSubmit, onCancel }: DeleteAccountFormProps) {
  const [password, setPassword] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!password) {
      setError("Enter your password to confirm.");
      return;
    }
    setError(null);
    setIsDeleting(true);
    try {
      await onSubmit(password);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete your account.");
      setIsDeleting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <p className="text-sm text-ink">
        Your account, all your projects, their documents, chat sessions and dashboard history are
        deleted. This can&apos;t be undone.
      </p>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Password
        <TextInput
          type="password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          autoComplete="current-password"
          autoFocus
        />
      </label>
      {error && (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onCancel} disabled={isDeleting}>
          Cancel
        </Button>
        <Button type="submit" variant="danger" disabled={isDeleting}>
          {isDeleting ? "Deleting…" : "Delete account"}
        </Button>
      </div>
    </form>
  );
}
