export type UserRole = 'candidate' | 'recruiter';

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface ContactInfo {
  name?: string;
  email?: string;
  phone?: string;
  location?: string;
  linkedin?: string;
  github?: string;
}

export interface EducationEntry {
  degree?: string;
  institution?: string;
  field?: string;
  year?: string;
  gpa?: string;
}

export interface ExperienceEntry {
  title?: string;
  company?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
  technologies?: string[];
}

export interface CertificationEntry {
  name?: string;
  issuer?: string;
  year?: string;
  url?: string;
}

export interface ProjectEntry {
  name?: string;
  description?: string;
  technologies?: string[];
  url?: string;
}

export interface ExtractedData {
  contact_info?: ContactInfo;
  skills?: string[];
  technical_skills?: string[];
  soft_skills?: string[];
  education?: EducationEntry[];
  experience?: ExperienceEntry[];
  certifications?: CertificationEntry[];
  projects?: ProjectEntry[];
  keywords?: string[];
  domain_knowledge?: string[];
  summary?: string;
  total_experience_years?: number;
  confidence_scores?: Record<string, number>;
  missing_fields?: string[];
  quality_score?: number;
  quality_suggestions?: string[];
}

export interface ResumeResponse {
  id: number;
  filename: string;
  file_type: string;
  file_size: number;
  is_analyzed: boolean;
  created_at: string;
}

export interface ResumeDetailResponse extends ResumeResponse {
  extracted_data?: ExtractedData;
}

export type WorkMode = 'remote' | 'onsite' | 'hybrid';
export type JobStatus = 'active' | 'closed' | 'draft';

export interface JobCreate {
  title: string;
  company: string;
  description: string;
  location?: string;
  work_mode?: WorkMode;
  experience_min?: number;
  experience_max?: number;
  salary_min?: number;
  salary_max?: number;
  required_skills?: string[];
  preferred_skills?: string[];
  education_requirements?: string[];
  certifications?: string[];
  responsibilities?: string[];
  technologies?: string[];
  seniority?: string;
  category?: string;
  status?: JobStatus;
}

export type JobUpdate = Partial<JobCreate>;

export interface JobResponse {
  id: number;
  recruiter_id: number;
  title: string;
  company: string;
  description: string;
  location?: string;
  work_mode: WorkMode;
  experience_min: number;
  experience_max: number;
  salary_min?: number;
  salary_max?: number;
  required_skills?: string[];
  preferred_skills?: string[];
  education_requirements?: string[];
  certifications?: string[];
  responsibilities?: string[];
  technologies?: string[];
  seniority?: string;
  category?: string;
  status: JobStatus;
  created_at: string;
  applicant_count?: number;
  is_saved?: boolean;
}

export interface PaginatedJobs {
  items: JobResponse[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export interface MatchScoreBreakdown {
  overall_score: number;
  skill_score: number;
  experience_score: number;
  education_score: number;
  semantic_score: number;
  project_score: number;
}

export interface MatchExplanation {
  summary?: string;
  matched_skills?: string[];
  missing_skills?: string[];
  partially_matched?: string[];
  strong_matches?: string[];
  recommendations?: string[];
  feature_contributions?: Record<string, number>;
  evidence?: Array<Record<string, any>>;
  scoring_method?: string;
  is_demo_mode?: boolean;
}

export interface MatchResponse {
  id: number;
  resume_id: number;
  job_id: number;
  scores: MatchScoreBreakdown;
  explanation: MatchExplanation;
  created_at: string;
}

export interface CandidateMatchItem {
  resume_id: number;
  candidate_name: string;
  candidate_email: string;
  overall_score: number;
  skill_score: number;
  experience_score: number;
  matched_skills?: string[];
  missing_skills?: string[];
  is_demo_mode?: boolean;
}

export interface CandidateRankingResponse {
  job_id: number;
  job_title: string;
  candidates: CandidateMatchItem[];
  total: number;
}

export interface JobMatchItem {
  job_id: number;
  job_title: string;
  company: string;
  location?: string;
  work_mode: WorkMode;
  overall_score: number;
  skill_score: number;
  matched_skills?: string[];
  missing_skills?: string[];
  is_demo_mode?: boolean;
}

export interface JobRecommendationResponse {
  resume_id: number;
  jobs: JobMatchItem[];
  total: number;
}

export type ApplicationStatus =
  | 'applied'
  | 'reviewing'
  | 'shortlisted'
  | 'interview'
  | 'offered'
  | 'rejected'
  | 'withdrawn';

export interface ApplicationCreate {
  job_id: number;
  resume_id: number;
  cover_letter?: string;
}

export interface ApplicationResponse {
  id: number;
  candidate_id: number;
  job_id: number;
  resume_id: number;
  status: ApplicationStatus;
  cover_letter?: string;
  applied_at: string;
  updated_at: string;
  job_title?: string;
  company?: string;
  candidate_name?: string;
  match_score?: number;
}

export interface CandidateAnalytics {
  total_resumes: number;
  analyzed_resumes: number;
  total_applications: number;
  applications_by_status: Record<string, number>;
  avg_match_score: number;
  top_match_score: number;
  top_skills: string[];
  skill_gaps: string[];
  recent_activity: Array<{
    type: string;
    description: string;
    timestamp: string;
    icon?: string;
  }>;
}

export interface RecruiterAnalytics {
  total_jobs: number;
  active_jobs: number;
  total_applications: number;
  applications_by_status: Record<string, number>;
  avg_match_score: number;
  pipeline_stats: Record<string, number>;
  skill_distribution: Record<string, number>;
  recent_activity: Array<{
    type: string;
    description: string;
    timestamp: string;
    icon?: string;
  }>;
}

export interface FairnessReport {
  report_type: string;
  metrics: Record<string, any>;
  limitations: string[];
  sample_size: number;
  generated_at: string;
  is_diagnostic: boolean;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  sources?: Array<{ title?: string; snippet?: string; score?: number }>;
  is_llm_generated?: boolean;
}

export interface ChatRequest {
  message: string;
  context?: {
    resume_id?: number;
    job_id?: number;
  };
}

export interface ChatResponse {
  response: string;
  sources?: Array<{ title?: string; snippet?: string; score?: number }>;
  is_llm_generated: boolean;
}

export interface SavedJob {
  id: number;
  job_id: number;
  candidate_id: number;
  saved_at: string;
  job?: JobResponse;
}
