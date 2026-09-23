"use client";

import { SignupForm } from "@/components/molecules/SignupForm";
import { useSignup } from "@/hooks/useSignup";

export function SignupPanel() {
  const { isSubmitting, error, submit } = useSignup();

  return <SignupForm onSubmit={submit} isSubmitting={isSubmitting} error={error} />;
}
