import { CodeBlock } from "@/components/atoms/CodeBlock";
import { FeedbackItem } from "@/components/molecules/FeedbackItem";
import type { ReviewedSnippet } from "@/types/review";

export function ReviewFeedbackPanel({ code, review }: ReviewedSnippet) {
  return (
    <div className="flex flex-col gap-4">
      <CodeBlock code={code} />
      <p className="text-sm text-ink">{review.summary}</p>
      {review.kind === "diff" && (
        <p className="text-xs text-muted">Reviewed as a diff: only added or changed lines.</p>
      )}
      {review.parse_error ? (
        <p role="alert" className="text-xs text-danger">
          {review.kind === "diff"
            ? review.parse_error
            : `${review.parse_error}. Check the snippet is complete and the language matches.`}
        </p>
      ) : review.findings.length === 0 ? (
        <p className="text-xs text-muted">No issues found.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {review.findings.map((finding, index) => (
            // Findings have no id; their position within one review never changes.
            <FeedbackItem key={index} {...finding} />
          ))}
        </ul>
      )}
      {!review.judgement_available && !review.parse_error && (
        <p role="status" className="text-xs text-muted">
          The model&apos;s review was not available, so only ESLint results are shown (accessibility,
          security and style rules; test coverage needs the model).
        </p>
      )}
      {review.notes.length > 0 && (
        <ul className="flex flex-col gap-1 text-xs text-muted">
          {review.notes.map((note) => (
            <li key={note}>Note: {note}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
