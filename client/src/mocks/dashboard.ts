import type { Activity } from "@/components/organisms/ActivityList";
import type { Stat } from "@/components/organisms/StatsGrid";

export const STATS: Stat[] = [
  { label: "Queries this week", value: 37 },
  { label: "Docs indexed", value: 12 },
  { label: "Reviews run", value: 9 },
];

export const ACTIVITY: Activity[] = [
  { id: "1", text: "How do I set up the dev environment?", timeAgo: "2m ago" },
  { id: "2", text: "Reviewed Card.tsx", timeAgo: "18m ago" },
  { id: "3", text: "What does the deployment diagram show?", timeAgo: "1h ago" },
];
