export type ReviewCategory = "accessibility" | "security" | "test" | "style";

export type SnippetLanguage = "tsx" | "ts" | "jsx" | "js";

export interface ReviewFinding {
  category: ReviewCategory;
  message: string;
  severity: "error" | "warning" | "suggestion";
  source: "eslint" | "model";
  line: number | null;
  rule_id: string | null;
  /** The changed file, when a diff was reviewed. */
  file: string | null;
}

export interface CodeReview {
  findings: ReviewFinding[];
  summary: string;
  /** False when the model's reply could not be read, so only ESLint findings are shown. */
  judgement_available: boolean;
  /** Set when the snippet is not valid code (or a diff has nothing reviewable). */
  parse_error: string | null;
  /** A pasted unified diff is detected and reviewed as one. */
  kind: "snippet" | "diff";
  /** What the review skipped, e.g. diff fragments ESLint can't parse on their own. */
  notes: string[];
}

/** A review together with the exact code it was run on. */
export interface ReviewedSnippet {
  code: string;
  review: CodeReview;
}
