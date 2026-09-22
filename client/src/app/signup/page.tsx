import Link from "next/link";
import { redirect } from "next/navigation";
import { AuthTemplate } from "@/components/templates/AuthTemplate";
import { getSession } from "@/lib/api/session";
import { SignupPanel } from "./SignupPanel";

export default async function SignupPage() {
  if (await getSession()) redirect("/dashboard");

  return (
    <AuthTemplate title="Create account">
      <SignupPanel />
      <p className="mt-4 text-center text-xs text-muted">
        Already have an account?{" "}
        <Link href="/login" className="font-medium text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthTemplate>
  );
}
