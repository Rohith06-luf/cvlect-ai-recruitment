import { createFileRoute } from "@tanstack/react-router";
import { AuthLayout, AuthForm } from "@/components/AuthLayout";

export const Route = createFileRoute("/candidate/auth")({
  head: () => ({ meta: [{ title: "Candidate Sign In — CVlect" }] }),
  component: CandidateAuth,
});

function CandidateAuth() {
  return (
    <AuthLayout
      title="Candidate sign in"
      subtitle="Track applications, improve your resume and find the right role."
      altText="New to CVlect?"
      altLinkText="Create candidate account"
      altLinkTo="/candidate/auth"
    >
      <AuthForm submitLabel="Sign in" onSubmitTo="/candidate/dashboard" createLabel="Create candidate account →" />
    </AuthLayout>
  );
}
