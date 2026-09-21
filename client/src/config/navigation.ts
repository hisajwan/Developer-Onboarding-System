export interface NavEntry {
  href: string;
  label: string;
}

export const NAV_ENTRIES: NavEntry[] = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/ask", label: "Ask" },
  { href: "/code-review", label: "Code review" },
];
