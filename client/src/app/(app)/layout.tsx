import { SidebarNav } from "@/components/organisms/SidebarNav";
import { AppShell } from "@/components/templates/AppShell";
import { NAV_ENTRIES } from "@/config/navigation";

export default function AppLayout({ children }: LayoutProps<"/">) {
  return <AppShell sidebar={<SidebarNav entries={NAV_ENTRIES} />}>{children}</AppShell>;
}
