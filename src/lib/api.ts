/**
 * API client for the CVlect FastAPI backend.
 *
 * Reads the backend URL from the VITE_API_URL env var. In development this is
 * set to http://localhost:8000 (see .env). In production, the same origin is
 * used because FastAPI serves the built frontend.
 */

const API_URL =
  (import.meta as any).env?.VITE_API_URL ??
  (typeof window !== "undefined" && window.location.origin ? "" : "http://localhost:8000");

export const BASE_URL = API_URL || "http://localhost:8000";

const TOKEN_KEY = "cvlect_token";

export function getToken(): string | null {
  if (typeof localStorage === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (typeof localStorage === "undefined") return;
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore */
    }
    if (res.status === 401) setToken(null);
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/* =========================================================
 * Types
 * ========================================================= */
export interface User {
  id: number;
  name: string;
  email: string;
  role: "recruiter" | "candidate";
  avatar_initials: string | null;
  phone: string | null;
  location: string | null;
  company: string | null;
  job_title: string | null;
  team: string | null;
  about: string | null;
  verified: boolean;
  created_at: string | null;
}

export interface TokenOut {
  token: string;
  user: User;
}

export interface Job {
  id: number;
  recruiter_id: number;
  title: string;
  company: string;
  location: string | null;
  salary: string | null;
  description: string | null;
  status: string;
  created_at: string | null;
}

export interface CandidateProfile {
  id: number;
  user_id: number;
  full_name: string;
  role: string | null;
  location: string | null;
  experience: string | null;
  summary: string | null;
  resume_path: string | null;
  resume_score: number;
  ats_score: number;
  keywords_score: number;
  experience_match: number;
  projects_score: number;
  education_score: number;
  achievements_score: number;
  career_health: number;
  current_skills: string[];
  missing_skills: string[];
  created_at: string | null;
}

export interface Application {
  id: number;
  candidate_id: number;
  job_id: number;
  status: string;
  applied_date: string;
  job_title: string | null;
  company: string | null;
  location: string | null;
  salary: string | null;
}

export interface PipelineEntry {
  id: number;
  recruiter_id: number;
  job_id: number;
  candidate_id: number;
  profile_id: number | null;
  score: number;
  rank: number;
  top_match: boolean;
  reason: string | null;
  status: string;
  created_at: string | null;
  name: string | null;
  role: string | null;
  location: string | null;
  experience: string | null;
  summary: string | null;
  matched: string[];
  missing: string[];
}

export interface Stats {
  total_resumes: number;
  shortlisted: number;
  selected: number;
  rejected: number;
}

export interface Activity {
  id: number;
  recruiter_id: number;
  text: string;
  created_at: string;
}

/* =========================================================
 * Auth
 * ========================================================= */
export const api = {
  signup: (body: {
    name: string;
    email: string;
    password: string;
    role: "recruiter" | "candidate";
    phone?: string;
    location?: string;
    company?: string;
    job_title?: string;
    team?: string;
    about?: string;
  }) => request<TokenOut>("/auth/signup", { method: "POST", body: JSON.stringify(body) }),

  login: (email: string, password: string) =>
    request<TokenOut>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  logout: () => request<{ message: string }>("/auth/logout", { method: "POST" }),

  me: () => request<User>("/auth/me"),

  /* Users */
  getUser: (id: number) => request<User>(`/users/${id}`),
  updateMe: (body: Partial<User>) =>
    request<User>("/users/me", { method: "PUT", body: JSON.stringify(body) }),

  /* Jobs */
  listJobs: (recruiterId?: number) =>
    request<Job[]>(`/jobs${recruiterId ? `?recruiter_id=${recruiterId}` : ""}`),
  createJob: (body: Partial<Job>) =>
    request<Job>("/jobs", { method: "POST", body: JSON.stringify(body) }),
  getJob: (id: number) => request<Job>(`/jobs/${id}`),

  /* Profiles */
  listProfiles: (userId?: number) =>
    request<CandidateProfile[]>(`/profiles${userId ? `?user_id=${userId}` : ""}`),
  getMyProfile: () => request<CandidateProfile>("/profiles/me"),
  uploadResume: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<CandidateProfile>("/profiles/upload-resume", {
      method: "POST",
      body: form as unknown as BodyInit,
      headers: {} as Record<string, string>, // let browser set multipart boundary
    });
  },

  /* Applications */
  listApplications: (candidateId?: number) =>
    request<Application[]>(`/applications${candidateId ? `?candidate_id=${candidateId}` : ""}`),
  listMyApplications: () => request<Application[]>("/applications/me"),
  createApplication: (jobId: number) =>
    request<Application>("/applications", {
      method: "POST",
      body: JSON.stringify({ job_id: jobId }),
    }),
  updateApplicationStatus: (id: number, status: string) =>
    request<Application>(`/applications/${id}/status?status=${encodeURIComponent(status)}`, {
      method: "PUT",
    }),

  /* Pipeline */
  listPipeline: (params: { jobId?: number; recruiterId?: number; page?: number; pageSize?: number }) => {
    const q = new URLSearchParams();
    if (params.jobId) q.set("job_id", String(params.jobId));
    if (params.recruiterId) q.set("recruiter_id", String(params.recruiterId));
    if (params.page) q.set("page", String(params.page));
    if (params.pageSize) q.set("page_size", String(params.pageSize));
    return request<PipelineEntry[]>(`/pipeline?${q.toString()}`);
  },
  countPipeline: (params: { jobId?: number; recruiterId?: number }) => {
    const q = new URLSearchParams();
    if (params.jobId) q.set("job_id", String(params.jobId));
    if (params.recruiterId) q.set("recruiter_id", String(params.recruiterId));
    return request<{ total: number }>(`/pipeline/count?${q.toString()}`);
  },
  updatePipelineStatus: (id: number, status: string) =>
    request<PipelineEntry>(`/pipeline/${id}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    }),
  ingestPdfToPipeline: (jobId: number, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<{ message: string; user_id: number; profile_id: number }>(
      `/pipeline/ingest-pdf?job_id=${jobId}`,
      { method: "POST", body: form as unknown as BodyInit, headers: {} as Record<string, string> },
    );
  },

  /* Stats */
  getStats: (params: { recruiterId?: number; jobId?: number }) => {
    const q = new URLSearchParams();
    if (params.recruiterId) q.set("recruiter_id", String(params.recruiterId));
    if (params.jobId) q.set("job_id", String(params.jobId));
    return request<Stats>(`/stats?${q.toString()}`);
  },

  /* Activities */
  listActivities: (recruiterId?: number, limit = 20) =>
    request<Activity[]>(
      `/activities${recruiterId ? `?recruiter_id=${recruiterId}&limit=${limit}` : `?limit=${limit}`}`,
    ),
};
