import type { ReactNode } from "react";
import { Heading } from "@/components/atoms/Heading";

export function PageTemplate({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="flex h-full flex-col gap-6">
      <Heading>{title}</Heading>
      {/* min-h-0 lets this shrink below its content's natural height, so a scrollable child
          (e.g. Ask's message list) can actually claim the overflow instead of growing past it. */}
      <div className="min-h-0 flex-1">{children}</div>
    </div>
  );
}
