import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

const SIZES = { h1: "text-lg", h2: "text-sm" } as const;

export function Heading({ as: Tag = "h1", children }: { as?: keyof typeof SIZES; children: ReactNode }) {
  return <Tag className={cn("font-bold text-ink", SIZES[Tag])}>{children}</Tag>;
}
