"use client";

import { useRouter } from "next/navigation";
import { useCallback, useState } from "react";
import { signup } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/http";
import type { SignupFields } from "@/types/auth";

export function useSignup() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = useCallback(
    async (fields: SignupFields) => {
      setError(null);
      setIsSubmitting(true);
      try {
        await signup(fields);
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
