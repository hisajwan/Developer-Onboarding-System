"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api/http";
import { reviewCode } from "@/lib/api/reviews";
import type { ReviewedSnippet, SnippetLanguage } from "@/types/review";

/** Reviews one snippet at a time for the current project; a project switch clears the result. */
export function useCodeReview(projectId: string | null) {
  const [result, setResult] = useState<ReviewedSnippet | null>(null);
  const [isReviewing, setIsReviewing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Ignore a reply that arrives after the project changed or a newer review started.
  const requestRef = useRef(0);

  useEffect(() => {
    function reset() {
      requestRef.current += 1;
      setResult(null);
      setError(null);
      setIsReviewing(false);
    }
    reset();
  }, [projectId]);

  const review = useCallback(
    async (code: string, language: SnippetLanguage) => {
      if (!projectId) return;
      const request = ++requestRef.current;
      setIsReviewing(true);
      setError(null);
      try {
        const data = await reviewCode(projectId, code, language);
        if (request === requestRef.current) setResult({ code, review: data });
      } catch (err) {
        if (request === requestRef.current) {
          setError(err instanceof ApiError ? err.message : "Could not review the snippet.");
        }
      } finally {
        if (request === requestRef.current) setIsReviewing(false);
      }
    },
    [projectId],
  );

  return { result, isReviewing, error, review };
}
