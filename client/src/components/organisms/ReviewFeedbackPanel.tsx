import { CodeBlock } from "@/components/atoms/CodeBlock";
import { FeedbackItem } from "@/components/molecules/FeedbackItem";
import type { ReviewFeedback } from "@/types/review";

export function ReviewFeedbackPanel({ code, feedback }: { code: string; feedback: ReviewFeedback[] }) {
  return (
    <div className="flex max-w-2xl flex-col gap-4">
      <CodeBlock code={code} />
      <ul className="flex flex-col gap-3">
        {feedback.map(({ id, ...item }) => (
          <FeedbackItem key={id} {...item} />
        ))}
      </ul>
    </div>
  );
}
