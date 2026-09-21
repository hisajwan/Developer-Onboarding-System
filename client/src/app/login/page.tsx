import { redirect } from "next/navigation";
import { AuthTemplate } from "@/components/templates/AuthTemplate";
import { getSession } from "@/lib/api/session";
import { LoginPanel } from "./LoginPanel";

export default async function LoginPage() {
  if (await getSession()) redirect("/dashboard");

  return (
    <AuthTemplate title="Sign in">
      <LoginPanel />
    </AuthTemplate>
  );
}
