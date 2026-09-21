export function ActivityRow({ text, timeAgo }: { text: string; timeAgo: string }) {
  return (
    <li className="flex items-baseline justify-between border-b border-border py-2 text-xs">
      <span>{text}</span>
      <span className="text-muted">{timeAgo}</span>
    </li>
  );
}
