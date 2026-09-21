"use client";

import { CodeReviewPanel } from "@/components/organisms/CodeReviewPanel";
import { PageTemplate } from "@/components/templates/PageTemplate";
import { useCodeReview } from "@/hooks/useCodeReview";
import { SAMPLE_CODE, SAMPLE_FEEDBACK, SAMPLE_NOTICE } from "@/mocks/codeReview";

export default function CodeReviewPage() {
  const { submittedCode, submit } = useCodeReview();

  return (
    <PageTemplate title="Code review">
      <CodeReviewPanel
        onSubmit={submit}
        submittedCode={submittedCode}
        feedback={SAMPLE_FEEDBACK}
        initialCode={SAMPLE_CODE}
        notice={SAMPLE_NOTICE}
      />
    </PageTemplate>
  );
}
