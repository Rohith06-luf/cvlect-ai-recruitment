import axios, { AxiosError } from 'axios';
import type {
  User,
  TokenResponse,
  ResumeResponse,
  ResumeDetailResponse,
  JobCreate,
  JobUpdate,
  JobResponse,
  PaginatedJobs,
  MatchResponse,
  CandidateRankingResponse,
  JobRecommendationResponse,
  ApplicationCreate,
  ApplicationResponse,
  CandidateAnalytics,
  RecruiterAnalytics,
  FairnessReport,
  ChatRequest,
  ChatResponse,
  SavedJob,
} from '../types';

const configuredApiUrl = import.meta.env.VITE_API_URL?.trim();
const normalizedApiUrl = configuredApiUrl?.replace(/\/+$/, '');
const API_BASE_URL =
  !normalizedApiUrl
    ? '/api'
    : /^https?:\/\/[^/]+$/i.test(normalizedApiUrl)
      ? `${normalizedApiUrl}/api`
      : normalizedApiUrl;

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle unauthorized errors
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      const currentPath = window.location.pathname;
      const requestUrl = error.config?.url || '';
      if (
        !currentPath.includes('/login') &&
        !currentPath.includes('/register') &&
        currentPath !== '/' &&
        !requestUrl.includes('/auth/login') &&
        !requestUrl.includes('/auth/register') &&
        !requestUrl.includes('/auth/me')
      ) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export const api = {
  auth: {
    register: async (data: { email: string; password: string; full_name: string; role: 'candidate' | 'recruiter' }) => {
      const response = await apiClient.post<TokenResponse>('/auth/register', data);
      return response.data;
    },
    login: async (data: { email: string; password: string }) => {
      const response = await apiClient.post<TokenResponse>('/auth/login', data);
      return response.data;
    },
    getMe: async () => {
      const response = await apiClient.get<User>('/auth/me');
      return response.data;
    },
  },

  resumes: {
    upload: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const response = await apiClient.post<ResumeResponse>('/resumes/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return response.data;
    },
    list: async () => {
      const response = await apiClient.get<ResumeResponse[]>('/resumes');
      return response.data;
    },
    get: async (id: number) => {
      const response = await apiClient.get<ResumeDetailResponse>(`/resumes/${id}`);
      return response.data;
    },
    analyze: async (id: number) => {
      const response = await apiClient.post<ResumeDetailResponse>(`/resumes/${id}/analyze`);
      return response.data;
    },
  },

  jobs: {
    create: async (data: JobCreate) => {
      const response = await apiClient.post<JobResponse>('/jobs', data);
      return response.data;
    },
    list: async (params?: {
      page?: number;
      per_page?: number;
      search?: string;
      location?: string;
      work_mode?: string;
      category?: string;
      recruiter_id?: number;
    }) => {
      const response = await apiClient.get<PaginatedJobs>('/jobs', { params });
      return response.data;
    },
    get: async (id: number) => {
      const response = await apiClient.get<JobResponse>(`/jobs/${id}`);
      return response.data;
    },
    update: async (id: number, data: JobUpdate) => {
      const response = await apiClient.put<JobResponse>(`/jobs/${id}`, data);
      return response.data;
    },
    delete: async (id: number) => {
      const response = await apiClient.delete<{ message: string }>(`/jobs/${id}`);
      return response.data;
    },
  },

  matching: {
    analyze: async (data: { resume_id: number; job_id: number }) => {
      const response = await apiClient.post<MatchResponse>('/matching/analyze', data);
      return response.data;
    },
    getCandidatesForJob: async (jobId: number, params?: { min_score?: number }) => {
      const response = await apiClient.get<CandidateRankingResponse>(`/matching/jobs/${jobId}/candidates`, {
        params,
      });
      return response.data;
    },
    getJobsForResume: async (resumeId: number, params?: { min_score?: number }) => {
      const response = await apiClient.get<JobRecommendationResponse>(`/matching/resumes/${resumeId}/jobs`, {
        params,
      });
      return response.data;
    },
    getExplanation: async (matchId: number) => {
      const response = await apiClient.get<MatchResponse>(`/matching/${matchId}/explanation`);
      return response.data;
    },
  },

  applications: {
    create: async (data: ApplicationCreate) => {
      const response = await apiClient.post<ApplicationResponse>('/applications', data);
      return response.data;
    },
    list: async (params?: { status?: string; job_id?: number }) => {
      const response = await apiClient.get<ApplicationResponse[]>('/applications', { params });
      return response.data;
    },
    updateStatus: async (id: number, status: string) => {
      const response = await apiClient.patch<ApplicationResponse>(`/applications/${id}/status`, { status });
      return response.data;
    },
  },

  analytics: {
    getCandidate: async () => {
      const response = await apiClient.get<CandidateAnalytics>('/analytics/candidate');
      return response.data;
    },
    getRecruiter: async () => {
      const response = await apiClient.get<RecruiterAnalytics>('/analytics/recruiter');
      return response.data;
    },
    getFairnessReports: async () => {
      const response = await apiClient.get<FairnessReport[]>('/analytics/fairness/reports');
      return response.data;
    },
  },

  assistant: {
    chat: async (data: ChatRequest) => {
      const response = await apiClient.post<ChatResponse>('/assistant/chat', data);
      return response.data;
    },
  },

  savedJobs: {
    save: async (jobId: number) => {
      const response = await apiClient.post<{ message: string; saved: boolean }>(`/saved-jobs/${jobId}`);
      return response.data;
    },
    unsave: async (jobId: number) => {
      const response = await apiClient.delete<{ message: string; saved: boolean }>(`/saved-jobs/${jobId}`);
      return response.data;
    },
    list: async () => {
      const response = await apiClient.get<SavedJob[]>('/saved-jobs');
      return response.data;
    },
  },
};
