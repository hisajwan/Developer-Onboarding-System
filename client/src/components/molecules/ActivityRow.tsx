import { Badge } from "@/components/atoms/Badge";

interface ActivityRowProps {
  kind: "question" | "review";
  title: string;
  detail: string;
  meta: string;
  when: string;
}

export function ActivityRow({ kind, title, detail, meta, when }: ActivityRowProps) {
  return (
    <li className="flex items-start gap-3 border-b border-border py-3 text-xs">
      <Badge tone={kind === "question" ? "primary" : "accent"}>
        {kind === "question" ? "Question" : "Review"}
      </Badge>
      <div className="min-w-0 flex-1">
        <p className="truncate text-ink">{title}</p>
        {detail && <p className="mt-0.5 line-clamp-2 text-muted">{detail}</p>}
        <p className="mt-1 text-muted">{meta}</p>
      </div>
      <span className="shrink-0 text-muted">{when}</span>
    </li>
  );
}
