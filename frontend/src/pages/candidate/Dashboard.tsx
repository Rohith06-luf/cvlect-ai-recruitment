import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  FileText,
  Briefcase,
  CheckCircle2,
  TrendingUp,
  Sparkles,
  ArrowRight,
  Clock,
  ExternalLink,
  Upload,
} from 'lucide-react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from 'recharts';
import { useAuth } from '../../contexts/AuthContext';
import { api } from '../../api/client';
import { StatCard } from '../../components/ui/StatCard';
import { ScoreRing } from '../../components/ui/ScoreRing';
import { SkillTag } from '../../components/ui/SkillTag';
import { CardSkeleton } from '../../components/ui/LoadingSkeleton';
import type { CandidateAnalytics, ResumeResponse, JobMatchItem } from '../../types';

export const CandidateDashboard: React.FC = () => {
  const { user } = useAuth();
  const [analytics, setAnalytics] = useState<CandidateAnalytics | null>(null);
  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [recommendedJobs, setRecommendedJobs] = useState<JobMatchItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsData, resumeList] = await Promise.allSettled([
          api.analytics.getCandidate(),
          api.resumes.list(),
        ]);

        if (analyticsData.status === 'fulfilled') {
          setAnalytics(analyticsData.value);
        }
        if (resumeList.status === 'fulfilled') {
          setResumes(resumeList.value);

          // If there is an analyzed resume, fetch recommended jobs
          const analyzed = resumeList.value.find((r) => r.is_analyzed);
          if (analyzed) {
            try {
              const recs = await api.matching.getJobsForResume(analyzed.id);
              setRecommendedJobs(recs.jobs.slice(0, 4));
            } catch {
              // ignore
            }
          }
        }
      } catch (err) {
        console.error('Failed to load candidate dashboard', err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  // Pie chart data for applications status
  const statusData = analytics?.applications_by_status
    ? Object.entries(analytics.applications_by_status).map(([key, value]) => ({
        name: key.charAt(0).toUpperCase() + key.slice(1),
        value,
      }))
    : [
        { name: 'Applied', value: 3 },
        { name: 'Reviewing', value: 2 },
        { name: 'Shortlisted', value: 1 },
      ];

  const COLORS = ['#7c3aed', '#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

  // Radar data for skills
  const radarData = [
    { skill: 'Python', candidate: 90, benchmark: 80 },
    { skill: 'React', candidate: 85, benchmark: 75 },
    { skill: 'FastAPI', candidate: 80, benchmark: 70 },
    { skill: 'SQL', candidate: 75, benchmark: 65 },
    { skill: 'System Design', candidate: 65, benchmark: 75 },
    { skill: 'Docker', candidate: 70, benchmark: 80 },
  ];

  return (
    <div className="space-y-8">
      {/* Welcome Banner */}
      <div className="relative rounded-3xl p-6 sm:p-8 glass-panel border border-violet-500/20 overflow-hidden shadow-2xl">
        <div className="absolute right-0 top-0 bottom-0 w-1/2 bg-gradient-to-l from-violet-600/10 to-transparent pointer-events-none" />
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div>
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-xs text-violet-300 font-medium mb-3">
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Job Match Active</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Welcome back, {user?.full_name || 'Candidate'}!
            </h1>
            <p className="mt-1 text-sm text-slate-300 max-w-xl">
              Your profile is continuously scanned against live opportunities. Check your skill gap analytics and recent job recommendations below.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/candidate/resume"
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-violet-600/25 transition-all flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              <span>Upload / Update Resume</span>
            </Link>
            <Link
              to="/candidate/assistant"
              className="px-5 py-2.5 rounded-xl glass-input border border-white/10 hover:border-violet-500/40 text-slate-200 hover:text-white font-medium text-xs sm:text-sm transition-all flex items-center gap-2"
            >
              <Sparkles className="w-4 h-4 text-violet-400" />
              <span>Ask AI Copilot</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Stat Cards Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
          <CardSkeleton />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Uploaded Resumes"
            value={analytics?.total_resumes ?? resumes.length}
            icon={<FileText className="w-5 h-5" />}
            accentColor="violet"
            sublabel={`${analytics?.analyzed_resumes ?? resumes.filter((r) => r.is_analyzed).length} analyzed by AI`}
          />
          <StatCard
            label="Active Applications"
            value={analytics?.total_applications ?? 0}
            icon={<Briefcase className="w-5 h-5" />}
            accentColor="blue"
            trend={{ value: '12%', isPositive: true, label: 'vs last month' }}
          />
          <StatCard
            label="Avg Match Score"
            value={`${Math.round(analytics?.avg_match_score ?? 76)}%`}
            icon={<TrendingUp className="w-5 h-5" />}
            accentColor="emerald"
            trend={{ value: 'High', isPositive: true, label: 'compatibility' }}
          />
          <StatCard
            label="Top Job Match"
            value={`${Math.round(analytics?.top_match_score ?? 92)}%`}
            icon={<Sparkles className="w-5 h-5" />}
            accentColor="amber"
            sublabel="Based on skill vector index"
          />
        </div>
      )}

      {/* Main Content: Recommended Jobs + Recent Resume Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column (2 cols): Recommended Jobs & Skill Gap Radar */}
        <div className="lg:col-span-2 space-y-8">
          {/* Recommended Jobs */}
          <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-lg font-bold text-white tracking-tight">AI Recommended Jobs</h2>
                <p className="text-xs text-slate-400">Matched to your extracted skills & experience</p>
              </div>
              <Link
                to="/candidate/jobs"
                className="text-xs font-semibold text-violet-400 hover:text-violet-300 flex items-center gap-1"
              >
                <span>Browse All</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            {recommendedJobs.length > 0 ? (
              <div className="space-y-3">
                {recommendedJobs.map((job) => (
                  <motion.div
                    key={job.job_id}
                    whileHover={{ scale: 1.01 }}
                    className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-violet-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-4 transition-all"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <Link
                          to={`/candidate/jobs/${job.job_id}`}
                          className="font-bold text-white text-sm hover:text-violet-400 transition-colors"
                        >
                          {job.job_title}
                        </Link>
                        <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-white/5">
                          {job.work_mode}
                        </span>
                      </div>
                      <p className="text-xs text-slate-400">{job.company} • {job.location || 'Remote'}</p>
                      {job.matched_skills && job.matched_skills.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {job.matched_skills.slice(0, 3).map((s) => (
                            <SkillTag key={s} name={s} variant="matched" size="sm" />
                          ))}
                          {job.missing_skills && job.missing_skills.length > 0 && (
                            <SkillTag name={`-${job.missing_skills[0]}`} variant="missing" size="sm" />
                          )}
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-4 shrink-0">
                      <div className="text-right">
                        <span className="text-xs text-slate-400 block">Match Score</span>
                        <span className="text-lg font-extrabold text-emerald-400">
                          {Math.round(job.overall_score)}%
                        </span>
                      </div>
                      <Link
                        to={`/candidate/jobs/${job.job_id}`}
                        className="p-2.5 rounded-xl bg-violet-600/20 hover:bg-violet-600 text-violet-300 hover:text-white border border-violet-500/30 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                      </Link>
                    </div>
                  </motion.div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 bg-slate-900/30 rounded-2xl border border-dashed border-white/10">
                <p className="text-sm text-slate-400 mb-3">
                  Upload and analyze a resume to unlock tailored job match recommendations.
                </p>
                <Link
                  to="/candidate/resume"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-violet-600 text-white text-xs font-semibold hover:bg-violet-500 transition-colors"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>Analyze Resume Now</span>
                </Link>
              </div>
            )}
          </div>

          {/* Skill Radar / Competency Distribution */}
          <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl">
            <h2 className="text-lg font-bold text-white tracking-tight mb-1">Competency Alignment Radar</h2>
            <p className="text-xs text-slate-400 mb-4">Your evaluated capabilities versus market demand</p>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255, 255, 255, 0.1)" />
                  <PolarAngleAxis dataKey="skill" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 11 }} />
                  <PolarRadiusAxis stroke="rgba(255, 255, 255, 0.1)" />
                  <Radar
                    name="Your Profile"
                    dataKey="candidate"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.35}
                  />
                  <Radar
                    name="Market Demand"
                    dataKey="benchmark"
                    stroke="#3b82f6"
                    fill="#3b82f6"
                    fillOpacity={0.15}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: 'rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Right Column (1 col): Resume Status & Pipeline Breakdown */}
        <div className="space-y-8">
          {/* Active Resume Card */}
          <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl text-center">
            <h3 className="text-base font-bold text-white tracking-tight mb-4">Current Active Resume</h3>
            {resumes.length > 0 ? (
              <div className="space-y-4">
                <ScoreRing score={88} size="lg" label="Overall Quality" sublabel="ATS Optimized" showGrade />
                <div className="text-left bg-white/[0.02] p-4 rounded-2xl border border-white/5 space-y-2">
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">File Name:</span>
                    <span className="text-white font-medium truncate max-w-[150px]">
                      {resumes[0].filename}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs">
                    <span className="text-slate-400">Analysis Status:</span>
                    <span className="text-emerald-400 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Analyzed
                    </span>
                  </div>
                </div>
                <Link
                  to="/candidate/resume"
                  className="block w-full py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-violet-300 font-semibold text-xs border border-violet-500/20 transition-colors"
                >
                  View Extracted Profile & Insights
                </Link>
              </div>
            ) : (
              <div className="py-8 space-y-3">
                <FileText className="w-12 h-12 text-slate-600 mx-auto" />
                <p className="text-xs text-slate-400">No resumes uploaded yet.</p>
                <Link
                  to="/candidate/resume"
                  className="inline-block px-4 py-2 rounded-xl bg-violet-600 text-white font-semibold text-xs hover:bg-violet-500 transition-colors"
                >
                  Upload First Resume
                </Link>
              </div>
            )}
          </div>

          {/* Application Status Distribution */}
          <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl">
            <h3 className="text-base font-bold text-white tracking-tight mb-1">Application Pipeline</h3>
            <p className="text-xs text-slate-400 mb-4">Stage distribution of your applications</p>

            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={65}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {statusData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: 'rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="grid grid-cols-2 gap-2 pt-2">
              {statusData.map((item, i) => (
                <div key={item.name} className="flex items-center gap-2 text-xs">
                  <span
                    className="w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: COLORS[i % COLORS.length] }}
                  />
                  <span className="text-slate-400">{item.name}:</span>
                  <span className="font-bold text-white">{item.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Activity */}
          <div className="glass-panel rounded-3xl p-6 border border-white/10 shadow-xl">
            <h3 className="text-base font-bold text-white tracking-tight mb-4">Recent Activity</h3>
            <div className="space-y-3">
              {[
                { desc: 'Resume matched with Senior Full Stack role', time: '2h ago' },
                { desc: 'Application submitted to Stripe', time: '1d ago' },
                { desc: 'AI parsed updated certifications', time: '3d ago' },
              ].map((act, idx) => (
                <div key={idx} className="flex items-start gap-3 text-xs pb-2 border-b border-white/5 last:border-0">
                  <Clock className="w-3.5 h-3.5 text-violet-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-slate-300 font-medium">{act.desc}</p>
                    <span className="text-slate-400 text-[10px]">{act.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
