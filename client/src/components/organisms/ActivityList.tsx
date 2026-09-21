import { Heading } from "@/components/atoms/Heading";
import { ActivityRow } from "@/components/molecules/ActivityRow";

export interface Activity {
  id: string;
  text: string;
  timeAgo: string;
}

export function ActivityList({ items }: { items: Activity[] }) {
  return (
    <section className="max-w-2xl">
      <Heading as="h2">Recent activity</Heading>
      {items.length === 0 ? (
        <p className="mt-3 text-xs text-muted">No activity yet.</p>
      ) : (
        <ul className="mt-2">
          {items.map(({ id, ...row }) => (
            <ActivityRow key={id} {...row} />
          ))}
        </ul>
      )}
    </section>
  );
}
