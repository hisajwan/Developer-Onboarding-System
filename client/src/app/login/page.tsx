import Link from "next/link";
import { redirect } from "next/navigation";
import { AuthTemplate } from "@/components/templates/AuthTemplate";
import { getSession } from "@/lib/api/session";
import { LoginPanel } from "./LoginPanel";

export default async function LoginPage() {
  if (await getSession()) redirect("/dashboard");

  return (
    <AuthTemplate title="Sign in">
      <LoginPanel />
      <p className="mt-4 text-center text-xs text-muted">
        Don&apos;t have an account?{" "}
        <Link href="/signup" className="font-medium text-primary hover:underline">
          Create one
        </Link>
      </p>
    </AuthTemplate>
  );
}
