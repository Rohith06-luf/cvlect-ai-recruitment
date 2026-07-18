import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  FileText,
  EyeOff,
  Activity,
  UserRound,
  Mail,
  Phone,
  MapPin,
  Building2,
  Briefcase,
  ArrowLeft,
} from "lucide-react";
import { Sidebar, type SidebarItem } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { GlassCard } from "@/components/GlassCard";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export const Route = createFileRoute("/recruiter/profile")({
  head: () => ({ meta: [{ title: "My Profile — CVlect" }] }),
  component: RecruiterProfile,
});

const items: SidebarItem[] = [
  { label: "Dashboard", to: "/recruiter/dashboard", icon: LayoutDashboard },
  { label: "Resumes", to: "/recruiter/dashboard", icon: FileText },
  { label: "Blind Hiring", to: "/recruiter/dashboard", icon: EyeOff },
  { label: "Activities", to: "/recruiter/dashboard", icon: Activity },
  { label: "My Profile", to: "/recruiter/profile", icon: UserRound },
];

function RecruiterProfile() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    location: "",
    company: "",
    job_title: "",
    team: "",
    about: "",
    avatar_url: "",
    social_links: "",
    password: "",
  });

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ["me"],
    queryFn: () => api.me(),
    enabled: !!user,
    retry: false,
  });

  useEffect(() => {
    if (!isEditing && profile) {
      setFormData({
        name: profile.name || "",
        phone: profile.phone || "",
        location: profile.location || "",
        company: profile.company || "",
        job_title: profile.job_title || "",
        team: profile.team || "",
        about: profile.about || "",
        avatar_url: profile.avatar_url || "",
        social_links: profile.social_links || "",
        password: "",
      });
    }
  }, [profile, isEditing]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex bg-background">
        <Sidebar items={items} />
        <div className="flex-1 min-w-0 flex flex-col">
          <Navbar title="My Profile" subtitle="Manage your account and preferences" profileTo="/recruiter/profile" />
          <main className="p-6 space-y-6">
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-primary)]" />
            </div>
          </main>
        </div>
      </div>
    );
  }

  if (error || !profile) {
    return (
      <div className="min-h-screen flex bg-background">
        <Sidebar items={items} />
        <div className="flex-1 min-w-0 flex flex-col">
          <Navbar title="My Profile" subtitle="Manage your account and preferences" profileTo="/recruiter/profile" />
          <main className="p-6 space-y-6">
            <GlassCard className="p-6 text-center">
              <p className="text-muted-foreground">Please log in to view your profile.</p>
            </GlassCard>
          </main>
        </div>
      </div>
    );
  }

  const initials = profile?.name
    ? profile.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : 'AR';

  const updateProfileMutation = useMutation({
    mutationFn: (data: typeof formData) => api.updateMe(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["me"] });
      setIsEditing(false);
    },
    onError: (err) => {
      console.error("Failed to update profile:", err);
      alert("Failed to update profile");
    },
  });

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(formData);
  };

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar items={items} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar title="My Profile" subtitle="Manage your account and preferences" />

        <main className="p-6 space-y-6">
          <Link
            to="/recruiter/dashboard"
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-white transition"
          >
            <ArrowLeft className="h-3.5 w-3.5" /> Back to dashboard
          </Link>

          <GlassCard className="p-6">
            <div className="flex items-center gap-5">
              <div className="h-20 w-20 rounded-2xl bg-gradient-to-br from-[var(--color-secondary)] to-[var(--color-primary)] grid place-items-center text-2xl font-semibold text-[var(--color-background)]">
                {initials}
              </div>
              <div>
                <h2 className="text-xl font-semibold">{profile?.name ?? 'Loading...'}</h2>
                <p className="text-sm text-muted-foreground">{profile?.job_title ?? 'Recruiter'} · {profile?.team ?? 'Talent Team'}</p>
                <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] text-[var(--color-success)] bg-[var(--color-success)]/15 rounded-full px-2 py-0.5">
                  Verified account
                </div>
              </div>
            </div>
          </GlassCard>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <GlassCard className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold">Contact</h3>
                  {isEditing && (
                    <button
                      type="button"
                      onClick={() => setIsEditing(false)}
                      className="text-xs text-muted-foreground hover:text-white"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
                <div className="space-y-3 text-sm">
                  <Row icon={Mail} label="Email" value={profile?.email ?? 'Not set'} />
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Phone</div>
                    <input
                      name="phone"
                      value={formData.phone}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                    />
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Location</div>
                    <input
                      name="location"
                      value={formData.location}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                    />
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Social Links</div>
                    <input
                      name="social_links"
                      value={formData.social_links}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                      placeholder="Twitter, LinkedIn, portfolio URLs"
                    />
                  </div>
                </div>
              </GlassCard>

              <GlassCard className="p-5">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-sm font-semibold">Work</h3>
                  {isEditing && (
                    <button
                      type="button"
                      onClick={() => setIsEditing(false)}
                      className="text-xs text-muted-foreground hover:text-white"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
                <div className="space-y-3 text-sm">
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Company</div>
                    <input
                      name="company"
                      value={formData.company}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                    />
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Role</div>
                    <input
                      name="job_title"
                      value={formData.job_title}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                    />
                  </div>
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Team</div>
                    <input
                      name="team"
                      value={formData.team}
                      onChange={handleChange}
                      disabled={!isEditing}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                    />
                  </div>
                </div>
              </GlassCard>
            </div>

            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold">About</h3>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="text-xs text-muted-foreground hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <textarea
                name="about"
                value={formData.about}
                onChange={handleChange}
                disabled={!isEditing}
                className="w-full min-h-[120px] bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                placeholder="Tell us about your recruiting experience"
              />
            </GlassCard>

            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold">Account</h3>
                {isEditing && (
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="text-xs text-muted-foreground hover:text-white"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="space-y-3 text-sm">
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Display Name</div>
                  <input
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                  />
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Profile Image URL</div>
                  <input
                    name="avatar_url"
                    value={formData.avatar_url}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                  />
                </div>
                <div>
                  <div className="text-[10px] uppercase tracking-wider text-muted-foreground mb-1">Password</div>
                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    disabled={!isEditing}
                    className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none disabled:text-muted-foreground/50"
                    placeholder="Leave blank to keep current password"
                  />
                </div>
              </div>
            </GlassCard>

            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <button
                    type="submit"
                    disabled={updateProfileMutation.isPending}
                    className="btn-glow rounded-xl bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium hover:brightness-110 transition"
                  >
                    {updateProfileMutation.isPending ? "Saving..." : "Save Changes"}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsEditing(false)}
                    className="rounded-xl border border-border bg-white/[0.03] px-4 py-2.5 text-sm font-medium hover:bg-white/[0.06] transition"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  type="button"
                  onClick={() => setIsEditing(true)}
                  className="btn-glow rounded-xl bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium hover:brightness-110 transition"
                >
                  Edit profile
                </button>
              )}
            </div>
          </form>
        </main>
      </div>
    </div>
  );
}

function Row({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <div className="h-8 w-8 rounded-lg border border-border bg-white/[0.03] grid place-items-center">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
        <div className="text-sm font-medium truncate">{value}</div>
      </div>
    </div>
  );
}
