"use client";

import { useState, type ChangeEvent, type FormEvent } from "react";
import { Button } from "@/components/atoms/Button";
import { TextInput } from "@/components/atoms/TextInput";
import { isValidEmail } from "@/lib/validation";
import type { SignupFields } from "@/types/auth";

interface SignupFormProps {
  onSubmit: (fields: SignupFields) => void;
  isSubmitting: boolean;
  error: string | null;
}

const EMPTY_FIELDS: SignupFields = {
  first_name: "",
  last_name: "",
  email: "",
  username: "",
  password: "",
};

export function SignupForm({ onSubmit, isSubmitting, error }: SignupFormProps) {
  const [fields, setFields] = useState<SignupFields>(EMPTY_FIELDS);
  const [confirmPassword, setConfirmPassword] = useState("");

  const emailLooksValid = fields.email === "" || isValidEmail(fields.email);
  const passwordsMatch = confirmPassword === "" || fields.password === confirmPassword;
  const canSubmit =
    Object.values(fields).every((value) => value !== "") &&
    confirmPassword !== "" &&
    isValidEmail(fields.email) &&
    fields.password === confirmPassword &&
    !isSubmitting;

  function set<K extends keyof SignupFields>(key: K) {
    return (event: ChangeEvent<HTMLInputElement>) =>
      setFields((current) => ({ ...current, [key]: event.target.value }));
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (canSubmit) onSubmit(fields);
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div className="flex gap-3">
        <label className="flex flex-1 flex-col gap-1 text-xs font-medium">
          First name
          <TextInput
            value={fields.first_name}
            onChange={set("first_name")}
            autoComplete="given-name"
            autoFocus
          />
        </label>
        <label className="flex flex-1 flex-col gap-1 text-xs font-medium">
          Last name
          <TextInput value={fields.last_name} onChange={set("last_name")} autoComplete="family-name" />
        </label>
      </div>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Email
        <TextInput type="email" value={fields.email} onChange={set("email")} autoComplete="email" />
        {!emailLooksValid && <span className="text-xs text-danger">Enter a valid email address.</span>}
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Username
        <TextInput value={fields.username} onChange={set("username")} autoComplete="username" />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Password
        <TextInput
          type="password"
          value={fields.password}
          onChange={set("password")}
          autoComplete="new-password"
          minLength={8}
        />
      </label>
      <label className="flex flex-col gap-1 text-xs font-medium">
        Confirm password
        <TextInput
          type="password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
          autoComplete="new-password"
          minLength={8}
        />
        {!passwordsMatch && <span className="text-xs text-danger">Passwords do not match.</span>}
      </label>
      {error && (
        <p role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
      <Button type="submit" disabled={!canSubmit}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </Button>
    </form>
  );
}
