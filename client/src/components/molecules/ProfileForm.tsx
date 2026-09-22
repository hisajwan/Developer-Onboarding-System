"use client";

import { useState, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { TextInput } from "@/components/atoms/TextInput";
import { ApiError } from "@/lib/api/http";
import type { Profile } from "@/types/profile";

interface ProfileFormProps {
  profile: Profile;
  onSave: (firstName: string, lastName: string) => Promise<Profile>;
}

export function ProfileForm({ profile, onSave }: ProfileFormProps) {
  const [firstName, setFirstName] = useState(profile.first_name);
  const [lastName, setLastName] = useState(profile.last_name);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = firstName.trim() !== "" && lastName.trim() !== "" && !isSaving;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!canSubmit) return;
    setError(null);
    setMessage(null);
    setIsSaving(true);
    try {
      await onSave(firstName.trim(), lastName.trim());
      setMessage("Saved.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save your changes.");
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <label className="flex flex-col gap-1 text-xs font-medium">
        First name
        <TextInput value={firstName} onChange={(event) => setFirstName(event.target.value)} />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Last name
        <TextInput value={lastName} onChange={(event) => setLastName(event.target.value)} />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Username
        <TextInput value={profile.username} disabled />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Email
        <TextInput value={profile.email} disabled />
      </label>
      {message && <p className="text-xs text-primary">{message}</p>}
      {error && (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
      <Button type="submit" disabled={!canSubmit}>
        {isSaving ? "Saving..." : "Save changes"}
      </Button>
    </form>
  );
}
