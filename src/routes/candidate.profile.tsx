import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import {
  LayoutDashboard,
  FileText,
  Briefcase,
  BarChart3,
  Settings,
  Mail,
  Phone,
  MapPin,
  Building2,
  LinkIcon,
  ArrowLeft,
  Save,
  X,
  Edit2,
} from "lucide-react";
import { Sidebar, type SidebarItem } from "@/components/Sidebar";
import { Navbar } from "@/components/Navbar";
import { GlassCard } from "@/components/GlassCard";
import { useAuth } from "@/lib/auth";
import { api } from "@/lib/api";
import { useQuery } from "@tanstack/react-query";

export const Route = createFileRoute("/candidate/profile")({
  head: () => ({ meta: [{ title: "My Profile — CVlect" }] }),
  component: CandidateProfile,
});

const items: SidebarItem[] = [
  { label: "Dashboard", to: "/candidate/dashboard", icon: LayoutDashboard },
  { label: "Applications", to: "/candidate/dashboard", icon: Briefcase },
  { label: "Resume", to: "/candidate/dashboard", icon: FileText },
  { label: "Skill Gap", to: "/candidate/dashboard", icon: BarChart3 },
  { label: "Settings", to: "/candidate/dashboard", icon: Settings },
];

function CandidateProfile() {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    full_name: "",
    role: "",
    location: "",
    experience: "",
    education: "",
    summary: "",
    phone: "",
    skills: "",
    company: "",
    designation: "",
    avatar_url: "",
    social_links: "",
    password: "",
  });

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ["my-profile"],
    queryFn: () => api.getMyProfile(),
    enabled: !!user,
    retry: false,
  });

  useEffect(() => {
    if (!isEditing && profile) {
      setFormData({
        full_name: profile.full_name || "",
        role: profile.role || "",
        location: profile.location || "",
        experience: profile.experience || "",
        education: profile.education || "",
        summary: profile.summary || "",
        phone: profile.phone || "",
        skills: profile.current_skills?.join(", ") || "",
        company: profile.company || "",
        designation: profile.designation || "",
        avatar_url: profile.avatar_url || "",
        social_links: profile.social_links || "",
        password: "",
      });
    }
  }, [profile, isEditing]);

  const updateProfileMutation = useMutation({
    mutationFn: (data: typeof formData) => api.updateProfile(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["my-profile"] });
      setIsEditing(false);
    },
    onError: (err) => {
      console.error("Failed to update profile:", err);
      alert("Failed to update profile");
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateProfileMutation.mutate(formData);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex bg-background">
        <Sidebar items={items} />
        <div className="flex-1 min-w-0 flex flex-col">
          <Navbar title="My Profile" subtitle="Manage your account and preferences" profileTo="/candidate/profile" />
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
          <Navbar title="My Profile" subtitle="Manage your account and preferences" profileTo="/candidate/profile" />
          <main className="p-6 space-y-6">
            <GlassCard className="p-6 text-center">
              <p className="text-muted-foreground">Please log in to view your profile.</p>
            </GlassCard>
          </main>
        </div>
      </div>
    );
  }

  const initials = profile?.full_name
    ? profile.full_name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : (user?.name || 'U').split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);

  return (
    <div className="min-h-screen flex bg-background">
      <Sidebar items={items} />
      <div className="flex-1 min-w-0 flex flex-col">
        <Navbar title="My Profile" subtitle="Manage your account and preferences" profileTo="/candidate/profile" />

        <main className="p-6 space-y-6">
          <Link
            to="/candidate/dashboard"
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
                {isEditing ? (
                  <input
                    type="text"
                    name="full_name"
                    value={formData.full_name}
                    onChange={handleChange}
                    className="text-xl font-semibold bg-transparent border-none outline-none text-white"
                  />
                ) : (
                  <h2 className="text-xl font-semibold">{profile?.full_name ?? user?.name ?? 'Loading...'}</h2>
                )}
                <p className="text-sm text-muted-foreground">{profile?.role ?? user?.role ?? 'Candidate'}</p>
                <div className="mt-2 inline-flex items-center gap-1.5 text-[11px] text-[var(--color-success)] bg-[var(--color-success)]/15 rounded-full px-2 py-0.5">
                  Verified account
                </div>
              </div>
            </div>
          </GlassCard>

          <form onSubmit={handleSubmit}>
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
                  <Row icon={Mail} label="Email" value={user?.email ?? 'Not set'} disabled />
                  <RowEdit
                    icon={Phone}
                    label="Phone"
                    name="phone"
                    value={formData.phone}
                    onChange={handleChange}
                    disabled={!isEditing}
                  />
                  <RowEdit
                    icon={MapPin}
                    label="Location"
                    name="location"
                    value={formData.location}
                    onChange={handleChange}
                    disabled={!isEditing}
                  />
                <RowEdit
                  icon={LinkIcon}
                  label="Social Links"
                  name="social_links"
                  value={formData.social_links}
                  onChange={handleChange}
                  disabled={!isEditing}
                />
                <RowEdit
                  icon={FileText}
                  label="Avatar URL"
                  name="avatar_url"
                  value={formData.avatar_url}
                  onChange={handleChange}
                  disabled={!isEditing}
                />
              </div>
            </GlassCard>

            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold">Professional</h3>
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
                <RowEdit
                  icon={Building2}
                  label="Current Role"
                  name="role"
                  value={formData.role || ""}
                  onChange={handleChange}
                  disabled={!isEditing}
                />
                <RowEdit
                  icon={Briefcase}
                  label="Company"
                  name="company"
                  value={formData.company}
                  onChange={handleChange}
                  disabled={!isEditing}
                />
                <RowEdit
                  icon={FileText}
                  label="Designation"
                  name="designation"
                  value={formData.designation}
                  onChange={handleChange}
                  disabled={!isEditing}
                />
                <RowEdit
                  icon={Building2}
                  label="Experience"
                  name="experience"
                  value={formData.experience}
                  onChange={handleChange}
                  disabled={!isEditing}
                  multiline
                />
              </div>
            </GlassCard>
            </div>

            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold">Summary</h3>
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
              {isEditing ? (
                <textarea
                  name="summary"
                  value={formData.summary}
                  onChange={handleChange}
                  className="w-full bg-transparent border-none outline-none text-sm text-white resize-none min-h-[80px]"
                  placeholder="Tell us about yourself..."
                />
              ) : (
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {profile?.summary ?? 'No summary added yet.'}
                </p>
              )}
            </GlassCard>

            <GlassCard className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold">Skills & Education</h3>
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
              {isEditing ? (
                <>
                  <div className="space-y-3">
                    <label className="block text-[10px] uppercase tracking-wider text-muted-foreground">Skills</label>
                    <input
                      name="skills"
                      value={formData.skills}
                      onChange={handleChange}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none"
                      placeholder="Comma-separated skills"
                    />
                    <label className="block text-[10px] uppercase tracking-wider text-muted-foreground">Education</label>
                    <input
                      name="education"
                      value={formData.education}
                      onChange={handleChange}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none"
                      placeholder="Your education summary"
                    />
                    <label className="block text-[10px] uppercase tracking-wider text-muted-foreground">New Password</label>
                    <input
                      type="password"
                      name="password"
                      value={formData.password}
                      onChange={handleChange}
                      className="w-full bg-transparent border border-border rounded-xl px-3 py-2 text-sm text-white outline-none"
                      placeholder="Leave blank to keep current password"
                    />
                  </div>
                </>
              ) : (
                <div className="space-y-3 text-sm">
                  <Row icon={Building2} label="Education" value={profile?.education || "Not set"} />
                  <div>
                    <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Skills</div>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {(profile?.current_skills && profile.current_skills.length > 0 ? profile.current_skills : ["Upload a resume to populate skills"]).map((skill) => (
                        <span key={skill} className="rounded-full bg-white/5 border border-white/5 px-3 py-1.5 text-xs">
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </GlassCard>

            <div className="flex gap-2">
              {isEditing ? (
                <>
                  <button
                    type="submit"
                    disabled={updateProfileMutation.isPending}
                    className="btn-glow rounded-xl bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium hover:brightness-110 transition flex items-center gap-2"
                  >
                    <Save className="h-4 w-4" />
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
                  className="btn-glow rounded-xl bg-[var(--color-primary)] px-4 py-2.5 text-sm font-medium hover:brightness-110 transition flex items-center gap-2"
                >
                  <Edit2 className="h-4 w-4" />
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

function RowEdit({
  icon: Icon,
  label,
  name,
  value,
  onChange,
  disabled,
  multiline = false,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  name: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => void;
  disabled: boolean;
  multiline?: boolean;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="h-8 w-8 rounded-lg border border-border bg-white/[0.03] grid place-items-center mt-1">
        <Icon className="h-4 w-4 text-muted-foreground" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</div>
        {multiline ? (
          <textarea
            name={name}
            value={value}
            onChange={onChange}
            disabled={disabled}
            rows={3}
            className="w-full bg-transparent border-none outline-none text-sm font-medium resize-none disabled:text-muted-foreground/50"
          />
        ) : (
          <input
            type="text"
            name={name}
            value={value}
            onChange={onChange}
            disabled={disabled}
            className="w-full bg-transparent border-none outline-none text-sm font-medium disabled:text-muted-foreground/50"
          />
        )}
      </div>
    </div>
  );
}

function Row({
  icon: Icon,
  label,
  value,
  disabled = false,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: string;
  disabled?: boolean;
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
