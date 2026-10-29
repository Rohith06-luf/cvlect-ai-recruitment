import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search,
  Eye,
  SlidersHorizontal,
  Mail,
} from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../components/ui/Toast';
import { ScoreRing } from '../../components/ui/ScoreRing';
import { SkillTag } from '../../components/ui/SkillTag';
import { TableSkeleton } from '../../components/ui/LoadingSkeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import { CandidateDetailModal } from './CandidateDetail';
import type { JobResponse, CandidateMatchItem } from '../../types';

export const CandidateSearch: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initialJobId = searchParams.get('job_id');

  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(
    initialJobId ? parseInt(initialJobId, 10) : null
  );
  const [candidates, setCandidates] = useState<CandidateMatchItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [minScore, setMinScore] = useState<number>(50);
  const [searchQuery, setSearchQuery] = useState('');

  // Selected candidate for detail view modal
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateMatchItem | null>(null);

  const toast = useToast();

  // Load jobs list for the dropdown
  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const data = await api.jobs.list({ per_page: 50 });
        setJobs(data.items);
        if (!selectedJobId && data.items.length > 0) {
          setSelectedJobId(data.items[0].id);
        }
      } catch (err) {
        console.error('Failed to load jobs for candidate ranking', err);
      }
    };

    fetchJobs();
  }, []);

  // Fetch candidates whenever selectedJobId or minScore changes
  useEffect(() => {
    if (!selectedJobId) return;

    const fetchRankings = async () => {
      setIsLoading(true);
      try {
        const result = await api.matching.getCandidatesForJob(selectedJobId, {
          min_score: minScore,
        });
        setCandidates(result.candidates);
      } catch (err) {
        toast.error('Error', 'Failed to calculate candidate ranking for this job.');
      } finally {
        setIsLoading(false);
      }
    };

    fetchRankings();
  }, [selectedJobId, minScore]);

  // Client-side natural language search across candidate names or skills
  const filteredCandidates = candidates.filter((c) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    const nameMatch = c.candidate_name.toLowerCase().includes(q);
    const emailMatch = c.candidate_email.toLowerCase().includes(q);
    const skillMatch = c.matched_skills?.some((s) => s.toLowerCase().includes(q));
    return nameMatch || emailMatch || skillMatch;
  });

  const selectedJob = jobs.find((j) => j.id === selectedJobId);

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          AI Candidate Ranking & Search
        </h1>
        <p className="mt-1 text-sm text-slate-300">
          Rank applicant profiles against job vectors with multi-factor explainable score breakdowns.
        </p>
      </div>

      {/* Control Panel: Job Selector & Search */}
      <div className="glass-panel p-6 rounded-3xl border border-white/10 shadow-xl space-y-5">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Job Selector */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Select Target Requisition to Rank Against
            </label>
            <select
              value={selectedJobId || ''}
              onChange={(e) => {
                const newId = parseInt(e.target.value, 10);
                setSelectedJobId(newId);
                setSearchParams({ job_id: String(newId) });
              }}
              className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white border border-white/10"
            >
              {jobs.map((job) => (
                <option key={job.id} value={job.id}>
                  {job.title} — {job.company} ({job.status})
                </option>
              ))}
            </select>
          </div>

          {/* Search Query */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Filter by Candidate Name or Skill
            </label>
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search candidate name or skill..."
                className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10"
              />
            </div>
          </div>
        </div>

        {/* Min Score Filter Slider */}
        <div className="pt-4 border-t border-white/10 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <SlidersHorizontal className="w-4 h-4 text-violet-400" />
            <span className="text-xs font-semibold text-slate-300">
              Minimum Compatibility Threshold: <strong className="text-violet-400">{minScore}%</strong>
            </span>
          </div>

          <div className="flex items-center gap-4 w-full sm:w-64">
            <span className="text-xs text-slate-500">0%</span>
            <input
              type="range"
              min={0}
              max={95}
              step={5}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-full accent-violet-500"
            />
            <span className="text-xs text-slate-500">95%</span>
          </div>
        </div>
      </div>

      {/* Target Job Overview Pill */}
      {selectedJob && (
        <div className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 flex flex-wrap items-center justify-between gap-4 text-xs">
          <div>
            <span className="text-slate-400">Target Role: </span>
            <strong className="text-white">{selectedJob.title}</strong>
            <span className="text-slate-500 ml-2">({selectedJob.work_mode})</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Required Skills:</span>
            {selectedJob.required_skills?.slice(0, 4).map((s) => (
              <span key={s} className="px-2 py-0.5 rounded bg-violet-500/20 text-violet-300 font-mono text-[11px]">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Candidate Ranking List */}
      {isLoading ? (
        <TableSkeleton rows={5} />
      ) : filteredCandidates.length > 0 ? (
        <div className="space-y-4">
          {filteredCandidates.map((candidate, idx) => (
            <motion.div
              key={candidate.resume_id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.05 }}
              onClick={() => setSelectedCandidate(candidate)}
              className="group p-5 rounded-3xl glass-panel border border-white/10 hover:border-violet-500/40 cursor-pointer shadow-xl transition-all flex flex-col md:flex-row md:items-center justify-between gap-6"
            >
              {/* Left Column: Candidate Info */}
              <div className="flex items-start gap-4">
                <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-violet-600 to-blue-600 flex items-center justify-center text-white font-extrabold text-base shadow-md shrink-0">
                  {candidate.candidate_name.charAt(0).toUpperCase()}
                </div>

                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-white group-hover:text-violet-300 transition-colors">
                      {candidate.candidate_name}
                    </h3>
                    <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-violet-500/20 text-violet-300 border border-violet-500/30">
                      Rank #{idx + 1}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-slate-500" />
                    <span>{candidate.candidate_email}</span>
                  </p>

                  {/* Skills badges */}
                  <div className="flex flex-wrap gap-1.5 pt-2">
                    {candidate.matched_skills?.slice(0, 4).map((skill) => (
                      <SkillTag key={skill} name={skill} variant="matched" size="sm" />
                    ))}
                    {candidate.missing_skills && candidate.missing_skills.length > 0 && (
                      <SkillTag
                        name={`-${candidate.missing_skills[0]}`}
                        variant="missing"
                        size="sm"
                      />
                    )}
                  </div>
                </div>
              </div>

              {/* Right Column: Score Breakdown and Action */}
              <div className="flex items-center justify-between md:justify-end gap-6 shrink-0 pt-4 md:pt-0 border-t md:border-t-0 border-white/5">
                <div className="flex items-center gap-4 text-center">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 block uppercase">
                      Skill Score
                    </span>
                    <span className="text-sm font-bold text-violet-300">
                      {Math.round(candidate.skill_score)}%
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 block uppercase">
                      Exp Score
                    </span>
                    <span className="text-sm font-bold text-blue-300">
                      {Math.round(candidate.experience_score)}%
                    </span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <ScoreRing
                    score={candidate.overall_score}
                    size="sm"
                    label=""
                  />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedCandidate(candidate);
                    }}
                    className="p-2.5 rounded-xl bg-violet-600/20 hover:bg-violet-600 text-violet-300 hover:text-white transition-colors"
                    title="View Comprehensive Diagnostic"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      ) : (
        <EmptyState
          title="No candidates match this criteria"
          description="Try lowering the minimum score threshold or selecting another active job requisition."
          actionLabel="Reset Score Filter"
          onAction={() => setMinScore(0)}
        />
      )}

      {/* Candidate Detail Modal */}
      {selectedCandidate && (
        <CandidateDetailModal
          candidate={selectedCandidate}
          jobId={selectedJobId}
          onClose={() => setSelectedCandidate(null)}
        />
      )}
    </div>
  );
};
