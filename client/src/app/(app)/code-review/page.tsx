"use client";

import { CodeReviewPanel } from "@/components/organisms/CodeReviewPanel";
import { PageTemplate } from "@/components/templates/PageTemplate";
import { useCodeReview } from "@/hooks/useCodeReview";
import { useProjectContext } from "../ProjectProvider";

export default function CodeReviewPage() {
  const { currentProjectId } = useProjectContext();
  const { result, isReviewing, error, review } = useCodeReview(currentProjectId);

  return (
    <PageTemplate title="Code review">
      <CodeReviewPanel onSubmit={review} isReviewing={isReviewing} result={result} error={error} />
    </PageTemplate>
  );
}
