import { Heading } from "@/components/atoms/Heading";
import { ActivityRow } from "@/components/molecules/ActivityRow";
import { timeAgo } from "@/lib/format";
import type { ActivityItem } from "@/types/stats";

function describe(item: ActivityItem): string {
  const where = item.source === "ask" ? "Ask" : "Code review screen";
  if (item.finding_count === null) return where;
  const findings = `${item.finding_count} finding${item.finding_count === 1 ? "" : "s"}`;
  return `${where} · ${findings}`;
}

export function ActivityList({ items }: { items: ActivityItem[] }) {
  return (
    <section className="max-w-2xl">
      <Heading as="h2">Recent activity</Heading>
      {items.length === 0 ? (
        <p className="mt-3 text-xs text-muted">
          No activity yet. Questions asked in Ask and reviews run in Code review appear here.
        </p>
      ) : (
        <ul className="mt-2">
          {items.map((item, index) => (
            // Items have no id; their order within one response never changes.
            <ActivityRow
              key={index}
              kind={item.kind}
              title={item.title}
              detail={item.detail}
              meta={describe(item)}
              when={timeAgo(item.created_at)}
            />
          ))}
        </ul>
      )}
    </section>
  );
}
