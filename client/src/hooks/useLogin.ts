"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { login } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/http";

export function useLogin() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (username: string, password: string) => {
      setError(null);
      setIsSubmitting(true);
      try {
        await login(username, password);
        router.replace("/dashboard");
        router.refresh();
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not reach the server.");
        setIsSubmitting(false);
      }
    },
    [router],
  );

  return { isSubmitting, error, submit };
}
