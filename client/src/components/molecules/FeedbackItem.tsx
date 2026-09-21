import { Badge, type BadgeTone } from "@/components/atoms/Badge";
import type { ReviewCategory } from "@/types/review";

const CATEGORY_TONE: Record<ReviewCategory, BadgeTone> = {
  a11y: "warning",
  test: "danger",
  style: "primary",
};

export function FeedbackItem({ category, message }: { category: ReviewCategory; message: string }) {
  return (
    <li className="flex items-center gap-3 text-xs text-muted">
      <Badge tone={CATEGORY_TONE[category]}>{category}</Badge>
      <span>{message}</span>
    </li>
  );
}
