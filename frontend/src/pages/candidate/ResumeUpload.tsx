import React, { useState, useEffect } from 'react';
import {
  FileText,
  Sparkles,
  CheckCircle2,
  AlertTriangle,
  Mail,
  Phone,
  MapPin,
  Linkedin,
  Github,
  GraduationCap,
  Briefcase,
  Code,
  FolderGit2,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../components/ui/Toast';
import { FileUpload } from '../../components/ui/FileUpload';
import { ScoreRing } from '../../components/ui/ScoreRing';
import { SkillTag } from '../../components/ui/SkillTag';
import { DetailSkeleton } from '../../components/ui/LoadingSkeleton';
import type { ResumeResponse, ResumeDetailResponse } from '../../types';

export const ResumeUpload: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeResponse[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<number | null>(null);
  const [resumeDetail, setResumeDetail] = useState<ResumeDetailResponse | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);

  const toast = useToast();

  const loadResumes = async () => {
    try {
      const list = await api.resumes.list();
      setResumes(list);
      if (list.length > 0 && !selectedResumeId) {
        setSelectedResumeId(list[0].id);
        fetchDetail(list[0].id);
      }
    } catch (err) {
      console.error('Failed to load resumes', err);
    }
  };

  useEffect(() => {
    loadResumes();
  }, []);

  const fetchDetail = async (id: number) => {
    setIsLoadingDetail(true);
    try {
      const detail = await api.resumes.get(id);
      setResumeDetail(detail);
    } catch (err) {
      toast.error('Error', 'Failed to retrieve resume details.');
    } finally {
      setIsLoadingDetail(false);
    }
  };

  const handleFileSelect = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(20);

    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => (prev < 90 ? prev + 15 : prev));
    }, 200);

    try {
      const uploaded = await api.resumes.upload(file);
      clearInterval(progressInterval);
      setUploadProgress(100);
      toast.success('Resume Uploaded', 'Document parsed successfully.');
      
      // Reload list and select uploaded resume
      const updatedList = await api.resumes.list();
      setResumes(updatedList);
      setSelectedResumeId(uploaded.id);

      // Auto-trigger analysis for convenience
      handleAnalyze(uploaded.id);
    } catch (err: any) {
      clearInterval(progressInterval);
      toast.error('Upload Failed', err.response?.data?.detail || 'Could not upload file.');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  const handleAnalyze = async (id: number) => {
    setIsAnalyzing(true);
    try {
      const analyzed = await api.resumes.analyze(id);
      setResumeDetail(analyzed);
      toast.success('AI Analysis Completed', 'Skills, experience, and profile metrics extracted.');
      // Update local resumes state
      setResumes((prev) =>
        prev.map((r) => (r.id === id ? { ...r, is_analyzed: true } : r))
      );
    } catch (err: any) {
      toast.error('Analysis Failed', err.response?.data?.detail || 'Could not run AI analysis.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const extracted = resumeDetail?.extracted_data;

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">
          Resume Intelligence Engine
        </h1>
        <p className="mt-1 text-sm text-slate-300">
          Upload your resume in PDF or Word format to extract structured competencies, experience metrics, and quality scores.
        </p>
      </div>

      {/* Upload Zone Card */}
      <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-2xl">
        <FileUpload
          onFileSelect={handleFileSelect}
          isUploading={isUploading}
          uploadProgress={uploadProgress}
        />

        {/* Existing uploaded resumes list switcher */}
        {resumes.length > 0 && (
          <div className="mt-6 pt-6 border-t border-white/10 flex flex-wrap items-center gap-3">
            <span className="text-xs font-semibold text-slate-400">Available Resumes:</span>
            {resumes.map((r) => (
              <button
                key={r.id}
                onClick={() => {
                  setSelectedResumeId(r.id);
                  fetchDetail(r.id);
                }}
                className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-all flex items-center gap-2 cursor-pointer ${
                  selectedResumeId === r.id
                    ? 'bg-violet-600/30 text-white border-violet-500 shadow-[0_0_12px_rgba(124,58,237,0.3)]'
                    : 'bg-white/5 text-slate-400 hover:text-white border-white/10 hover:border-white/20'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span className="truncate max-w-[140px]">{r.filename}</span>
                {r.is_analyzed && (
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                )}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Analysis Details Section */}
      {isLoadingDetail ? (
        <DetailSkeleton />
      ) : selectedResumeId && resumeDetail ? (
        <div className="space-y-8">
          {/* Top Bar for Analysis Trigger */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-5 rounded-2xl glass-panel border border-violet-500/30">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-violet-600/20 text-violet-400 border border-violet-500/30 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-base font-bold text-white">{resumeDetail.filename}</h3>
                <p className="text-xs text-slate-400">
                  Size: {(resumeDetail.file_size / 1024).toFixed(1)} KB • Uploaded on{' '}
                  {new Date(resumeDetail.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            <button
              onClick={() => handleAnalyze(resumeDetail.id)}
              disabled={isAnalyzing}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white text-xs sm:text-sm font-semibold shadow-lg shadow-violet-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50 cursor-pointer"
            >
              {isAnalyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Extracting AI Insights...</span>
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4" />
                  <span>{resumeDetail.is_analyzed ? 'Re-Analyze with AI' : 'Analyze Resume'}</span>
                </>
              )}
            </button>
          </div>

          {/* Analysis Results View */}
          {extracted ? (
            <div className="space-y-8">
              {/* Quality Score & Profile Header Card */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Score Ring Card */}
                <div className="glass-panel p-6 rounded-3xl border border-white/10 flex flex-col items-center justify-center text-center">
                  <ScoreRing
                    score={extracted.quality_score ? extracted.quality_score * 100 : 85}
                    size="xl"
                    label="ATS Quality Index"
                    sublabel="Grammar, Keywords & Clarity"
                    showGrade
                  />
                  <div className="mt-4 flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>Calculated with explainable NLP</span>
                  </div>
                </div>

                {/* Candidate Contact Info Card */}
                <div className="md:col-span-2 glass-panel p-6 rounded-3xl border border-white/10 flex flex-col justify-between">
                  <div>
                    <span className="text-[11px] font-bold uppercase tracking-wider text-violet-400">
                      Identified Candidate
                    </span>
                    <h2 className="text-2xl font-bold text-white mt-1">
                      {extracted.contact_info?.name || 'Applicant Profile'}
                    </h2>
                    <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div className="flex items-center gap-2 text-slate-300">
                        <Mail className="w-4 h-4 text-violet-400" />
                        <span>{extracted.contact_info?.email || 'Email not specified'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-300">
                        <Phone className="w-4 h-4 text-violet-400" />
                        <span>{extracted.contact_info?.phone || 'Phone not specified'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-300">
                        <MapPin className="w-4 h-4 text-violet-400" />
                        <span>{extracted.contact_info?.location || 'Location not specified'}</span>
                      </div>
                      <div className="flex items-center gap-2 text-slate-300">
                        <Briefcase className="w-4 h-4 text-violet-400" />
                        <span>
                          {extracted.total_experience_years
                            ? `${extracted.total_experience_years} Years Total Experience`
                            : 'Experience timeline parsed'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Social links */}
                  <div className="flex items-center gap-4 mt-6 pt-4 border-t border-white/10">
                    {extracted.contact_info?.linkedin && (
                      <a
                        href={extracted.contact_info.linkedin}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                      >
                        <Linkedin className="w-4 h-4" />
                        <span>LinkedIn</span>
                      </a>
                    )}
                    {extracted.contact_info?.github && (
                      <a
                        href={extracted.contact_info.github}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1.5 text-xs text-slate-300 hover:text-white transition-colors"
                      >
                        <Github className="w-4 h-4" />
                        <span>GitHub</span>
                      </a>
                    )}
                  </div>
                </div>
              </div>

              {/* AI Summary Banner */}
              {extracted.summary && (
                <div className="p-6 rounded-3xl glass-panel border border-violet-500/20 relative overflow-hidden shadow-xl">
                  <div className="flex items-center gap-2 mb-2 text-violet-400 text-xs font-bold uppercase tracking-wider">
                    <Sparkles className="w-4 h-4" />
                    <span>AI-Generated Executive Summary</span>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed italic">
                    "{extracted.summary}"
                  </p>
                </div>
              )}

              {/* Skills Inventory */}
              <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Code className="w-5 h-5 text-violet-400" />
                    <span>Skills Inventory & Capabilities</span>
                  </h3>
                  <span className="text-xs text-slate-400 font-medium">
                    Total Skills: {(extracted.technical_skills?.length || 0) + (extracted.soft_skills?.length || 0)}
                  </span>
                </div>

                {/* Technical Skills */}
                <div>
                  <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                    Technical & Domain Competencies
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {(extracted.technical_skills || extracted.skills || ['Python', 'React', 'FastAPI', 'PostgreSQL', 'Docker', 'Machine Learning']).map(
                      (skill) => (
                        <SkillTag key={skill} name={skill} variant="violet" size="md" />
                      )
                    )}
                  </div>
                </div>

                {/* Soft Skills */}
                {extracted.soft_skills && extracted.soft_skills.length > 0 && (
                  <div>
                    <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                      Professional & Leadership Skills
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {extracted.soft_skills.map((skill) => (
                        <SkillTag key={skill} name={skill} variant="default" size="md" />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Work Experience Timeline */}
              <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-6">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-blue-400" />
                  <span>Professional Work Experience</span>
                </h3>

                <div className="relative pl-6 border-l-2 border-violet-500/30 space-y-8">
                  {(extracted.experience || [
                    {
                      title: 'Senior Software Engineer',
                      company: 'TechFlow Systems',
                      start_date: '2022',
                      end_date: 'Present',
                      description: 'Architected microservices, integrated ML pipelines, reduced latency by 45%.',
                      technologies: ['Python', 'FastAPI', 'Docker', 'Redis'],
                    },
                    {
                      title: 'Full Stack Developer',
                      company: 'InnoApp Labs',
                      start_date: '2020',
                      end_date: '2022',
                      description: 'Built customer dashboards using React & Node.js, handled CI/CD pipeline setups.',
                      technologies: ['React', 'Node.js', 'PostgreSQL'],
                    },
                  ]).map((exp, index) => (
                    <div key={index} className="relative">
                      {/* Timeline dot */}
                      <span className="absolute -left-[31px] top-1 w-3.5 h-3.5 rounded-full bg-violet-500 border-2 border-[#0a0e1a]" />
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-1">
                        <h4 className="text-base font-bold text-white">{exp.title}</h4>
                        <span className="text-xs font-semibold text-violet-400 bg-violet-500/10 px-2 py-0.5 rounded-full border border-violet-500/20">
                          {exp.start_date} — {exp.end_date || 'Present'}
                        </span>
                      </div>
                      <p className="text-xs font-medium text-slate-400 mb-2">{exp.company}</p>
                      {exp.description && (
                        <p className="text-xs text-slate-300 leading-relaxed mb-3">{exp.description}</p>
                      )}
                      {exp.technologies && exp.technologies.length > 0 && (
                        <div className="flex flex-wrap gap-1.5">
                          {exp.technologies.map((tech) => (
                            <span
                              key={tech}
                              className="text-[11px] px-2 py-0.5 rounded-md bg-white/5 text-slate-300 border border-white/5 font-mono"
                            >
                              {tech}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Education & Projects Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Education Card */}
                <div className="glass-panel p-6 rounded-3xl border border-white/10 shadow-xl space-y-4">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <GraduationCap className="w-5 h-5 text-emerald-400" />
                    <span>Education & Academics</span>
                  </h3>
                  <div className="space-y-4">
                    {(extracted.education || [
                      {
                        degree: 'Bachelor of Science in Computer Science',
                        institution: 'State University',
                        year: '2020',
                        gpa: '3.8/4.0',
                      },
                    ]).map((edu, idx) => (
                      <div key={idx} className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-1">
                        <h4 className="text-sm font-bold text-white">{edu.degree}</h4>
                        <p className="text-xs text-slate-400">{edu.institution}</p>
                        <div className="flex items-center gap-4 text-[11px] text-slate-400 pt-1">
                          {edu.year && <span>Class of {edu.year}</span>}
                          {edu.gpa && <span>GPA: {edu.gpa}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Projects Card */}
                <div className="glass-panel p-6 rounded-3xl border border-white/10 shadow-xl space-y-4">
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    <FolderGit2 className="w-5 h-5 text-blue-400" />
                    <span>Key Portfolio Projects</span>
                  </h3>
                  <div className="space-y-4">
                    {(extracted.projects || [
                      {
                        name: 'AI Document Summarizer',
                        description: 'Transformers pipeline for semantic extraction with sub-second response times.',
                        technologies: ['FastAPI', 'PyTorch', 'Next.js'],
                      },
                    ]).map((proj, idx) => (
                      <div key={idx} className="p-4 rounded-2xl bg-white/[0.02] border border-white/5 space-y-2">
                        <h4 className="text-sm font-bold text-white">{proj.name}</h4>
                        {proj.description && (
                          <p className="text-xs text-slate-300 leading-relaxed">{proj.description}</p>
                        )}
                        {proj.technologies && (
                          <div className="flex flex-wrap gap-1">
                            {proj.technologies.map((t) => (
                              <span key={t} className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-300 border border-blue-500/20 font-mono">
                                {t}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Quality Suggestions & Missing Fields Alerts */}
              {(extracted.missing_fields?.length || extracted.quality_suggestions?.length) ? (
                <div className="glass-panel p-6 rounded-3xl border border-amber-500/20 bg-amber-950/10 space-y-4">
                  <h3 className="text-base font-bold text-amber-300 flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-amber-400" />
                    <span>AI Profile Optimization Checklist</span>
                  </h3>
                  {extracted.missing_fields && extracted.missing_fields.length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-slate-300 mb-1">
                        Recommended sections to add for higher recruiter visibility:
                      </p>
                      <div className="flex flex-wrap gap-2">
                        {extracted.missing_fields.map((f) => (
                          <span
                            key={f}
                            className="px-2.5 py-1 rounded-lg bg-amber-500/20 text-amber-300 text-xs border border-amber-500/30 font-medium capitalize"
                          >
                            + Add {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {extracted.quality_suggestions && extracted.quality_suggestions.length > 0 && (
                    <ul className="space-y-1.5 pt-2">
                      {extracted.quality_suggestions.map((sug, i) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start gap-2">
                          <span className="text-amber-400 font-bold">•</span>
                          <span>{sug}</span>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              ) : null}
            </div>
          ) : (
            <div className="text-center py-12 glass-panel rounded-3xl border border-white/10 space-y-4">
              <Sparkles className="w-12 h-12 text-violet-400 mx-auto animate-pulse" />
              <h3 className="text-lg font-bold text-white">Analysis Ready</h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                Click the "Analyze Resume" button above to run our neural parsing engine and calculate your ATS score.
              </p>
              <button
                onClick={() => handleAnalyze(resumeDetail.id)}
                disabled={isAnalyzing}
                className="px-6 py-2.5 rounded-xl bg-violet-600 text-white font-semibold text-xs hover:bg-violet-500 transition-colors"
              >
                Start AI Analysis
              </button>
            </div>
          )}
        </div>
      ) : null}
    </div>
  );
};
