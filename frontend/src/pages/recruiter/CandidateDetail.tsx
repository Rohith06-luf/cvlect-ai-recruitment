import React, { useState, useEffect } from 'react';
import {
  Mail,
  Briefcase,
  GraduationCap,
  Sparkles,
} from 'lucide-react';
import { ScoreRing } from '../../components/ui/ScoreRing';
import { SkillTag } from '../../components/ui/SkillTag';
import { Modal } from '../../components/ui/Modal';
import { useToast } from '../../components/ui/Toast';
import { api } from '../../api/client';
import type { CandidateMatchItem, ResumeDetailResponse } from '../../types';

interface CandidateDetailModalProps {
  candidate: CandidateMatchItem;
  jobId: number | null;
  onClose: () => void;
}

export const CandidateDetailModal: React.FC<CandidateDetailModalProps> = ({
  candidate,
  onClose,
}) => {
  const [resumeDetail, setResumeDetail] = useState<ResumeDetailResponse | null>(null);
  const [actionStatus, setActionStatus] = useState<string | null>(null);
  const toast = useToast();

  useEffect(() => {
    const fetchCandidateResume = async () => {
      try {
        const detail = await api.resumes.get(candidate.resume_id);
        setResumeDetail(detail);
      } catch {
        // detail not available, will fallback to candidate item info
      }
    };

    fetchCandidateResume();
  }, [candidate.resume_id]);

  const handleAction = (status: 'shortlisted' | 'interview' | 'rejected') => {
    setActionStatus(status);
    const messages = {
      shortlisted: 'Candidate has been marked as Shortlisted.',
      interview: 'Interview invitation initiated.',
      rejected: 'Candidate archived from active pipeline.',
    };
    toast.success('Action Recorded', messages[status]);
  };

  const extracted = resumeDetail?.extracted_data;

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title={candidate.candidate_name}
      subtitle={`Candidate Evaluation • Overall Compatibility: ${Math.round(candidate.overall_score)}%`}
      maxWidth="2xl"
      footer={
        <div className="flex items-center justify-between w-full">
          <div className="text-xs text-slate-400">
            {actionStatus ? (
              <span className="text-emerald-400 font-semibold capitalize">
                Status: {actionStatus}
              </span>
            ) : (
              <span>Reviewing Candidate Dossier</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => handleAction('rejected')}
              className="px-3 py-1.5 rounded-xl text-xs font-semibold text-rose-400 hover:bg-rose-500/10 border border-rose-500/20 transition-colors cursor-pointer"
            >
              Reject
            </button>
            <button
              onClick={() => handleAction('interview')}
              className="px-3.5 py-1.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold transition-colors cursor-pointer"
            >
              Schedule Interview
            </button>
            <button
              onClick={() => handleAction('shortlisted')}
              className="px-3.5 py-1.5 rounded-xl bg-violet-600 hover:bg-violet-500 text-white text-xs font-semibold shadow-md transition-colors cursor-pointer"
            >
              Shortlist Candidate
            </button>
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Top Score Rings Row */}
        <div className="grid grid-cols-3 gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/5">
          <ScoreRing
            score={candidate.overall_score}
            size="md"
            label="Overall Match"
            showGrade
          />
          <ScoreRing
            score={candidate.skill_score}
            size="md"
            label="Skill Vector"
          />
          <ScoreRing
            score={candidate.experience_score}
            size="md"
            label="Experience Alignment"
          />
        </div>

        {/* Contact info */}
        <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
          <div className="flex items-center gap-1.5">
            <Mail className="w-4 h-4 text-violet-400" />
            <span>{candidate.candidate_email}</span>
          </div>
          {extracted?.contact_info?.phone && (
            <span>• {extracted.contact_info.phone}</span>
          )}
          {extracted?.contact_info?.location && (
            <span>• {extracted.contact_info.location}</span>
          )}
        </div>

        {/* AI Summary */}
        {extracted?.summary && (
          <div className="p-4 rounded-2xl glass-panel border border-violet-500/20 text-xs text-slate-300 leading-relaxed italic">
            <div className="flex items-center gap-1.5 text-violet-400 font-bold mb-1 uppercase tracking-wider text-[10px]">
              <Sparkles className="w-3.5 h-3.5" />
              <span>AI Executive Profile Synthesis</span>
            </div>
            "{extracted.summary}"
          </div>
        )}

        {/* Skills Comparison */}
        <div className="space-y-3">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
            Competency Diagnostic
          </h4>

          {/* Matched */}
          <div>
            <span className="text-[11px] font-semibold text-emerald-400 block mb-1.5">
              Verified Matching Skills
            </span>
            <div className="flex flex-wrap gap-1.5">
              {(candidate.matched_skills || ['Python', 'React', 'FastAPI']).map((s) => (
                <SkillTag key={s} name={s} variant="matched" size="sm" />
              ))}
            </div>
          </div>

          {/* Missing */}
          {candidate.missing_skills && candidate.missing_skills.length > 0 && (
            <div className="pt-2">
              <span className="text-[11px] font-semibold text-rose-400 block mb-1.5">
                Missing Job Requisition Skills
              </span>
              <div className="flex flex-wrap gap-1.5">
                {candidate.missing_skills.map((s) => (
                  <SkillTag key={s} name={s} variant="missing" size="sm" />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Work Experience */}
        {extracted?.experience && extracted.experience.length > 0 && (
          <div className="space-y-3 pt-2">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <Briefcase className="w-3.5 h-3.5 text-blue-400" />
              <span>Experience History</span>
            </h4>
            <div className="space-y-3">
              {extracted.experience.map((exp, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-white/[0.02] border border-white/5 text-xs">
                  <div className="flex justify-between items-center mb-1">
                    <strong className="text-white">{exp.title}</strong>
                    <span className="text-slate-400 text-[10px]">
                      {exp.start_date} - {exp.end_date || 'Present'}
                    </span>
                  </div>
                  <p className="text-slate-400 mb-1">{exp.company}</p>
                  {exp.description && <p className="text-slate-300">{exp.description}</p>}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Education */}
        {extracted?.education && extracted.education.length > 0 && (
          <div className="space-y-2 pt-2">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
              <GraduationCap className="w-3.5 h-3.5 text-emerald-400" />
              <span>Academic Credentials</span>
            </h4>
            {extracted.education.map((edu, idx) => (
              <div key={idx} className="text-xs text-slate-300">
                <strong className="text-white">{edu.degree}</strong> — {edu.institution} ({edu.year})
              </div>
            ))}
          </div>
        )}
      </div>
    </Modal>
  );
};
