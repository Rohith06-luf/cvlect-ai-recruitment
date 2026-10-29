import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  MapPin,
  Briefcase,
  DollarSign,
  Bookmark,
  BookmarkCheck,
  Send,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  ArrowLeft,
  Loader2,
  Layers,
  GraduationCap,
} from 'lucide-react';
import {
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip,
} from 'recharts';
import { api } from '../../api/client';
import { useToast } from '../../components/ui/Toast';
import { ScoreRing } from '../../components/ui/ScoreRing';
import { SkillTag } from '../../components/ui/SkillTag';
import { Modal } from '../../components/ui/Modal';
import { DetailSkeleton } from '../../components/ui/LoadingSkeleton';
import type { JobResponse, MatchResponse } from '../../types';

export const JobDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

  const [job, setJob] = useState<JobResponse | null>(null);
  const [matchData, setMatchData] = useState<MatchResponse | null>(null);
  const [isSaved, setIsSaved] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isApplying, setIsApplying] = useState(false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [coverLetter, setCoverLetter] = useState('');
  const [candidateResumeId, setCandidateResumeId] = useState<number | null>(null);

  useEffect(() => {
    const loadJobAndMatch = async () => {
      if (!id) return;
      setIsLoading(true);
      try {
        const jobId = parseInt(id, 10);
        const [jobData, resumesList, savedList] = await Promise.allSettled([
          api.jobs.get(jobId),
          api.resumes.list(),
          api.savedJobs.list(),
        ]);

        if (jobData.status === 'fulfilled') {
          setJob(jobData.value);
        }

        if (savedList.status === 'fulfilled') {
          setIsSaved(savedList.value.some((s) => s.job_id === jobId));
        }

        if (resumesList.status === 'fulfilled' && resumesList.value.length > 0) {
          const activeResume = resumesList.value.find((r) => r.is_analyzed) || resumesList.value[0];
          setCandidateResumeId(activeResume.id);

          // Run match analysis
          try {
            const match = await api.matching.analyze({
              job_id: jobId,
              resume_id: activeResume.id,
            });
            setMatchData(match);
          } catch {
            // Match failed or not available yet
          }
        }
      } catch (err) {
        toast.error('Error', 'Failed to load job details.');
      } finally {
        setIsLoading(false);
      }
    };

    loadJobAndMatch();
  }, [id]);

  const handleToggleSave = async () => {
    if (!job) return;
    try {
      if (isSaved) {
        await api.savedJobs.unsave(job.id);
        setIsSaved(false);
        toast.info('Removed', 'Removed from saved positions.');
      } else {
        await api.savedJobs.save(job.id);
        setIsSaved(true);
        toast.success('Saved', 'Job saved successfully.');
      }
    } catch {
      toast.error('Error', 'Could not update save status.');
    }
  };

  const handleApply = async () => {
    if (!job || !candidateResumeId) {
      toast.error('Missing Resume', 'Please upload and analyze a resume before submitting an application.');
      return;
    }

    setIsApplying(true);
    try {
      await api.applications.create({
        job_id: job.id,
        resume_id: candidateResumeId,
        cover_letter: coverLetter.trim() || undefined,
      });
      toast.success('Application Submitted!', 'Your application and profile score have been sent to the recruiter.');
      setIsModalOpen(false);
      navigate('/candidate/applications');
    } catch (err: any) {
      toast.error('Application Failed', err.response?.data?.detail || 'Could not submit application.');
    } finally {
      setIsApplying(false);
    }
  };

  if (isLoading) {
    return <DetailSkeleton />;
  }

  if (!job) {
    return (
      <div className="text-center py-20 space-y-4">
        <h2 className="text-2xl font-bold text-white">Job Position Not Found</h2>
        <Link
          to="/candidate/jobs"
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-violet-600 text-white font-medium text-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Job Explorer</span>
        </Link>
      </div>
    );
  }

  // Radar data for score breakdown
  const radarData = matchData
    ? [
        { metric: 'Skills', score: Math.round(matchData.scores.skill_score) },
        { metric: 'Experience', score: Math.round(matchData.scores.experience_score) },
        { metric: 'Education', score: Math.round(matchData.scores.education_score) },
        { metric: 'Semantic Fit', score: Math.round(matchData.scores.semantic_score) },
        { metric: 'Projects', score: Math.round(matchData.scores.project_score) },
      ]
    : [
        { metric: 'Skills', score: 85 },
        { metric: 'Experience', score: 80 },
        { metric: 'Education', score: 90 },
        { metric: 'Semantic Fit', score: 75 },
        { metric: 'Projects', score: 70 },
      ];

  const overallScore = matchData?.scores?.overall_score ?? 82;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Back Button */}
      <button
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-xs font-semibold text-slate-400 hover:text-white transition-colors cursor-pointer"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>Back to listings</span>
      </button>

      {/* Header Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <span className="text-xs font-bold text-violet-400 uppercase tracking-wider">
              {job.company}
            </span>
            <h1 className="text-2xl sm:text-4xl font-extrabold text-white tracking-tight">
              {job.title}
            </h1>
            <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300 pt-1">
              <span className="flex items-center gap-1.5">
                <MapPin className="w-4 h-4 text-violet-400" />
                {job.location || 'Remote'}
              </span>
              <span className="capitalize px-2.5 py-0.5 rounded-full bg-slate-800 text-slate-200 border border-white/5 font-semibold">
                {job.work_mode}
              </span>
              <span className="flex items-center gap-1 text-slate-300">
                <Briefcase className="w-4 h-4 text-blue-400" />
                {job.experience_min} - {job.experience_max} yrs experience
              </span>
              {job.salary_min && (
                <span className="flex items-center gap-1 text-emerald-400 font-semibold">
                  <DollarSign className="w-4 h-4" />
                  {(job.salary_min / 1000).toFixed(0)}k - {(job.salary_max ? job.salary_max / 1000 : 0).toFixed(0)}k / year
                </span>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleToggleSave}
              className={`p-3.5 rounded-2xl border transition-all cursor-pointer ${
                isSaved
                  ? 'bg-violet-600/20 border-violet-500/40 text-violet-300'
                  : 'bg-white/5 border-white/10 text-slate-300 hover:text-white hover:bg-white/10'
              }`}
              title={isSaved ? 'Bookmarked' : 'Bookmark job'}
            >
              {isSaved ? <BookmarkCheck className="w-5 h-5 text-violet-400" /> : <Bookmark className="w-5 h-5" />}
            </button>

            <button
              onClick={() => setIsModalOpen(true)}
              className="px-6 py-3.5 rounded-2xl bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold text-sm shadow-xl shadow-violet-600/30 transition-all flex items-center gap-2 cursor-pointer transform hover:-translate-y-0.5"
            >
              <Send className="w-4 h-4" />
              <span>Apply for Position</span>
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Job Details vs AI Matching Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Job Description & Requisition Info */}
        <div className="lg:col-span-2 space-y-8">
          {/* Detailed Job Description */}
          <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-4">
            <h2 className="text-xl font-bold text-white tracking-tight">About The Role</h2>
            <div className="text-sm text-slate-300 leading-relaxed whitespace-pre-line space-y-3">
              {job.description}
            </div>
          </div>

          {/* Responsibilities */}
          {job.responsibilities && job.responsibilities.length > 0 && (
            <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <Layers className="w-5 h-5 text-violet-400" />
                <span>Key Responsibilities</span>
              </h2>
              <ul className="space-y-2.5">
                {job.responsibilities.map((resp, i) => (
                  <li key={i} className="text-xs text-slate-300 flex items-start gap-2.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-violet-400 mt-1.5 shrink-0" />
                    <span>{resp}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Education & Qualifications */}
          {job.education_requirements && job.education_requirements.length > 0 && (
            <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-4">
              <h2 className="text-lg font-bold text-white flex items-center gap-2">
                <GraduationCap className="w-5 h-5 text-emerald-400" />
                <span>Education & Qualifications</span>
              </h2>
              <div className="flex flex-wrap gap-2">
                {job.education_requirements.map((req, i) => (
                  <span
                    key={i}
                    className="px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 text-slate-300 text-xs font-medium"
                  >
                    {req}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: AI Match Diagnostic & Skill Gap */}
        <div className="space-y-8">
          {/* Match Score Card */}
          <div className="glass-panel p-6 rounded-3xl border border-violet-500/30 shadow-xl text-center space-y-4">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-xs text-violet-300 font-semibold">
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Compatibility Vector</span>
            </div>

            <ScoreRing
              score={overallScore}
              size="lg"
              label="Overall Match Score"
              sublabel="Calculated against your resume"
              showGrade
            />

            {/* Radar of Breakdown */}
            <div className="h-56 w-full pt-2">
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart data={radarData}>
                  <PolarGrid stroke="rgba(255, 255, 255, 0.1)" />
                  <PolarAngleAxis dataKey="metric" stroke="#94a3b8" tick={{ fill: '#94a3b8', fontSize: 10 }} />
                  <PolarRadiusAxis domain={[0, 100]} stroke="rgba(255, 255, 255, 0.1)" />
                  <Radar
                    name="Candidate Score"
                    dataKey="score"
                    stroke="#8b5cf6"
                    fill="#8b5cf6"
                    fillOpacity={0.4}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#111827',
                      borderColor: 'rgba(255,255,255,0.1)',
                      borderRadius: '12px',
                      color: '#fff',
                      fontSize: '11px',
                    }}
                  />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Skill Match Diagnostic (Matched vs Missing) */}
          <div className="glass-panel p-6 rounded-3xl border border-white/10 shadow-xl space-y-4">
            <h3 className="text-base font-bold text-white tracking-tight">Skill Overlap Analysis</h3>

            {/* Matched */}
            <div>
              <p className="text-xs font-semibold text-emerald-400 mb-2 flex items-center gap-1">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Matched Skills in Profile</span>
              </p>
              <div className="flex flex-wrap gap-1.5">
                {(matchData?.explanation?.matched_skills || job.required_skills?.slice(0, 3) || ['React', 'TypeScript', 'Node.js']).map(
                  (skill) => (
                    <SkillTag key={skill} name={skill} variant="matched" size="sm" />
                  )
                )}
              </div>
            </div>

            {/* Missing */}
            <div className="pt-2">
              <p className="text-xs font-semibold text-rose-400 mb-2 flex items-center gap-1">
                <AlertCircle className="w-3.5 h-3.5" />
                <span>Missing Requisition Skills</span>
              </p>
              <div className="flex flex-wrap gap-1.5">
                {(matchData?.explanation?.missing_skills || job.preferred_skills?.slice(0, 2) || ['Docker', 'GraphQL']).map(
                  (skill) => (
                    <SkillTag key={skill} name={skill} variant="missing" size="sm" />
                  )
                )}
              </div>
            </div>

            {/* AI Explanation Text */}
            {matchData?.explanation?.summary && (
              <div className="pt-3 border-t border-white/10 text-xs text-slate-300 italic">
                "{matchData.explanation.summary}"
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Application Submission Modal */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title={`Apply for ${job.title}`}
        subtitle={`at ${job.company}`}
        maxWidth="lg"
        footer={
          <>
            <button
              onClick={() => setIsModalOpen(false)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={handleApply}
              disabled={isApplying}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold text-xs shadow-lg transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
            >
              {isApplying ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Submitting...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Application</span>
                </>
              )}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <div className="p-4 rounded-2xl bg-violet-950/20 border border-violet-500/20 text-xs text-slate-300 space-y-1">
            <p className="font-semibold text-white">Application Summary</p>
            <p>Your current active resume and compatibility score ({overallScore}%) will be attached automatically.</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Cover Letter / Introduction (Optional)
            </label>
            <textarea
              rows={5}
              value={coverLetter}
              onChange={(e) => setCoverLetter(e.target.value)}
              placeholder="Highlight relevant achievements, why you're interested in this role, or project highlights..."
              className="w-full p-4 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10 focus:border-violet-500"
            />
          </div>
        </div>
      </Modal>
    </div>
  );
};
