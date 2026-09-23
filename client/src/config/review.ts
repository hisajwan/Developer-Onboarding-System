import type { ReviewCategory, SnippetLanguage } from "@/types/review";

/** Tag text per category, as in the wireframe (a11y / test / style). */
export const CATEGORY_LABELS: Record<ReviewCategory, string> = {
  accessibility: "a11y",
  test: "test",
  style: "style",
};

export const SNIPPET_LANGUAGES: { value: SnippetLanguage; label: string }[] = [
  { value: "tsx", label: "TSX" },
  { value: "ts", label: "TypeScript" },
  { value: "jsx", label: "JSX" },
  { value: "js", label: "JavaScript" },
];
