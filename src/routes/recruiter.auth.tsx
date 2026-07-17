import { createFileRoute } from "@tanstack/react-router";
import { AuthLayout, AuthForm } from "@/components/AuthLayout";

export const Route = createFileRoute("/recruiter/auth")({
  head: () => ({ meta: [{ title: "Recruiter Sign In — CVlect" }] }),
  component: RecruiterAuth,
});

function RecruiterAuth() {
  return (
    <AuthLayout
      title="Recruiter sign in"
      subtitle="Access your hiring dashboard and candidate pipeline."
      altText="New to CVlect?"
      altLinkText="Create recruiter account"
      altLinkTo="/recruiter/auth"
    >
      <AuthForm submitLabel="Sign in" onSubmitTo="/recruiter/dashboard" createLabel="Create recruiter account →" />
    </AuthLayout>
  );
}
