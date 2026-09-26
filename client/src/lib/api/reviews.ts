import type { CodeReview, SnippetLanguage } from "@/types/review";
import { apiFetch } from "./http";

export function reviewCode(
  projectId: string,
  code: string,
  language: SnippetLanguage,
): Promise<CodeReview> {
  return apiFetch<CodeReview>(`/projects/${projectId}/reviews`, {
    method: "POST",
    body: JSON.stringify({ code, language }),
  });
}
