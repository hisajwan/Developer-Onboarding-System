export type ReviewCategory = "a11y" | "test" | "style";

export interface ReviewFeedback {
  id: string;
  category: ReviewCategory;
  message: string;
}
