"use client";

import { LoginForm } from "@/components/molecules/LoginForm";
import { useLogin } from "@/hooks/useLogin";

export function LoginPanel() {
  const { isSubmitting, error, submit } = useLogin();

  return <LoginForm onSubmit={submit} isSubmitting={isSubmitting} error={error} />;
}
