import type { ReviewFeedback } from "@/types/review";

export const SAMPLE_CODE = `function Card({data}) {
  return <div>{data.title}</div>
}`;

export const SAMPLE_FEEDBACK: ReviewFeedback[] = [
  { id: "1", category: "a11y", message: "Missing alt text handling for image props" },
  { id: "2", category: "test", message: "No test coverage for this component" },
  { id: "3", category: "style", message: "Destructure props for readability" },
];

export const SAMPLE_NOTICE = "Sample feedback only: automated review is not connected yet, so this is the same for any code.";
