import { Heading } from "@/components/atoms/Heading";
import { CodeReviewForm } from "@/components/molecules/CodeReviewForm";
import { ReviewFeedbackPanel } from "@/components/organisms/ReviewFeedbackPanel";
import type { ReviewFeedback } from "@/types/review";

interface CodeReviewPanelProps {
  onSubmit: (code: string) => void;
  submittedCode: string | null;
  feedback: ReviewFeedback[];
  initialCode?: string;
  notice?: string;
}

export function CodeReviewPanel({ onSubmit, submittedCode, feedback, initialCode, notice }: CodeReviewPanelProps) {
  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <CodeReviewForm onSubmit={onSubmit} initialCode={initialCode} />
      {submittedCode === null ? (
        <p className="text-xs text-muted">Paste a snippet above and press Review to see feedback here.</p>
      ) : (
        <section className="flex flex-col gap-3" aria-live="polite">
          <Heading as="h2">Review feedback</Heading>
          <ReviewFeedbackPanel code={submittedCode} feedback={feedback} />
          {notice && (
            <p role="status" className="text-xs text-muted">
              {notice}
            </p>
          )}
        </section>
      )}
    </div>
  );
}
