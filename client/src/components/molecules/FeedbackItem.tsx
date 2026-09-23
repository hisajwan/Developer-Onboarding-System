import { Badge, type BadgeTone } from "@/components/atoms/Badge";
import { CATEGORY_LABELS } from "@/config/review";
import type { ReviewCategory, ReviewFinding } from "@/types/review";

const CATEGORY_TONE: Record<ReviewCategory, BadgeTone> = {
  accessibility: "warning",
  test: "danger",
  style: "primary",
};

export function FeedbackItem({ category, message, line, rule_id, source }: ReviewFinding) {
  const details = [
    line !== null && `Line ${line}`,
    rule_id,
    source === "eslint" ? "ESLint" : "Model suggestion",
  ].filter(Boolean);

  return (
    <li className="flex items-start gap-3 text-xs">
      <Badge tone={CATEGORY_TONE[category]}>{CATEGORY_LABELS[category]}</Badge>
      <div className="flex flex-col gap-0.5">
        <span className="text-ink">{message}</span>
        <span className="text-muted">{details.join(" · ")}</span>
      </div>
    </li>
  );
}
