import { Heading } from "@/components/atoms/Heading";
import { CodeReviewForm } from "@/components/molecules/CodeReviewForm";
import { ReviewFeedbackPanel } from "@/components/organisms/ReviewFeedbackPanel";
import type { ReviewedSnippet, SnippetLanguage } from "@/types/review";

interface CodeReviewPanelProps {
  onSubmit: (code: string, language: SnippetLanguage) => void;
  isReviewing: boolean;
  result: ReviewedSnippet | null;
  error: string | null;
}

export function CodeReviewPanel({ onSubmit, isReviewing, result, error }: CodeReviewPanelProps) {
  return (
    <div className="flex max-w-2xl flex-col gap-6">
      <CodeReviewForm onSubmit={onSubmit} isReviewing={isReviewing} />
      <section className="flex flex-col gap-3" aria-live="polite">
        {error && (
          <p role="alert" className="text-xs text-danger">
            {error}
          </p>
        )}
        {result ? (
          <>
            <Heading as="h2">Review feedback</Heading>
            <ReviewFeedbackPanel {...result} />
          </>
        ) : (
          !error && (
            <p className="text-xs text-muted">
              {isReviewing ? "Reviewing…" : "Paste a snippet above and press Review to see feedback here."}
            </p>
          )
        )}
      </section>
    </div>
  );
}
