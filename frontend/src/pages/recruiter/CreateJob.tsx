import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Building,
  MapPin,
  DollarSign,
  X,
  Sparkles,
  ArrowRight,
  Loader2,
  Layers,
} from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../components/ui/Toast';
import { SkillTag } from '../../components/ui/SkillTag';
import type { JobCreate, WorkMode, JobStatus } from '../../types';

export const CreateJob: React.FC = () => {
  const navigate = useNavigate();
  const toast = useToast();

  const [isSubmitting, setIsSubmitting] = useState(false);

  // Form Fields
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('');
  const [description, setDescription] = useState('');
  const [location, setLocation] = useState('');
  const [workMode, setWorkMode] = useState<WorkMode>('remote');
  const [seniority, setSeniority] = useState('Senior');
  const [category, setCategory] = useState('Engineering');
  const [status, setStatus] = useState<JobStatus>('active');

  const [experienceMin, setExperienceMin] = useState<number>(2);
  const [experienceMax, setExperienceMax] = useState<number>(6);
  const [salaryMin, setSalaryMin] = useState<string>('90000');
  const [salaryMax, setSalaryMax] = useState<string>('140000');

  // Tag list inputs
  const [requiredSkills, setRequiredSkills] = useState<string[]>(['Python', 'React', 'FastAPI']);
  const [newSkillInput, setNewSkillInput] = useState('');

  const [preferredSkills, setPreferredSkills] = useState<string[]>(['Docker', 'PostgreSQL', 'TailwindCSS']);
  const [newPreferredInput, setNewPreferredInput] = useState('');

  const [educationReqs, setEducationReqs] = useState<string[]>(["Bachelor's in Computer Science or related"]);
  const [newEduInput, setNewEduInput] = useState('');

  const [responsibilities, setResponsibilities] = useState<string[]>([
    'Design and maintain scalable microservice architectures.',
    'Collaborate with product and AI research teams to deliver end-to-end features.',
    'Write clean, unit-tested code and perform constructive peer reviews.',
  ]);
  const [newRespInput, setNewRespInput] = useState('');

  // Add tag helpers
  const handleAddSkill = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newSkillInput.trim()) {
      e.preventDefault();
      if (!requiredSkills.includes(newSkillInput.trim())) {
        setRequiredSkills([...requiredSkills, newSkillInput.trim()]);
      }
      setNewSkillInput('');
    }
  };

  const handleAddPreferred = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newPreferredInput.trim()) {
      e.preventDefault();
      if (!preferredSkills.includes(newPreferredInput.trim())) {
        setPreferredSkills([...preferredSkills, newPreferredInput.trim()]);
      }
      setNewPreferredInput('');
    }
  };

  const handleAddEdu = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && newEduInput.trim()) {
      e.preventDefault();
      if (!educationReqs.includes(newEduInput.trim())) {
        setEducationReqs([...educationReqs, newEduInput.trim()]);
      }
      setNewEduInput('');
    }
  };

  const handleAddResp = (e: React.FormEvent) => {
    e.preventDefault();
    if (newRespInput.trim()) {
      setResponsibilities([...responsibilities, newRespInput.trim()]);
      setNewRespInput('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !company || !description) {
      toast.error('Validation Error', 'Please complete title, company, and description.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: JobCreate = {
        title,
        company,
        description,
        location: location.trim() || undefined,
        work_mode: workMode,
        seniority,
        category,
        status,
        experience_min: Number(experienceMin),
        experience_max: Number(experienceMax),
        salary_min: salaryMin ? parseInt(salaryMin, 10) : undefined,
        salary_max: salaryMax ? parseInt(salaryMax, 10) : undefined,
        required_skills: requiredSkills,
        preferred_skills: preferredSkills,
        education_requirements: educationReqs,
        responsibilities,
        technologies: [...requiredSkills, ...preferredSkills],
      };

      await api.jobs.create(payload);
      toast.success('Job Published!', 'Requisition created and live for candidate matching.');
      navigate('/recruiter/jobs');
    } catch (err: any) {
      toast.error('Submission Failed', err.response?.data?.detail || 'Could not publish job.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 pb-12">
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Post New Requisition</h1>
        <p className="mt-1 text-sm text-slate-300">
          Define job specifications to enable automated vector indexing and candidate scoring.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {/* Core Info */}
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-5">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Briefcase className="w-4 h-4 text-violet-400" />
            <span>Role Fundamentals</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Job Title *
              </label>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Senior Full Stack Engineer"
                className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Company Name *
              </label>
              <div className="relative">
                <Building className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  required
                  value={company}
                  onChange={(e) => setCompany(e.target.value)}
                  placeholder="Apex Technologies"
                  className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10"
                />
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Location
              </label>
              <div className="relative">
                <MapPin className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="San Francisco, CA (or Remote)"
                  className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Work Mode
              </label>
              <select
                value={workMode}
                onChange={(e) => setWorkMode(e.target.value as WorkMode)}
                className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white border border-white/10"
              >
                <option value="remote">Remote</option>
                <option value="hybrid">Hybrid</option>
                <option value="onsite">Onsite</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Seniority Level
              </label>
              <select
                value={seniority}
                onChange={(e) => setSeniority(e.target.value)}
                className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white border border-white/10"
              >
                <option value="Entry">Entry Level</option>
                <option value="Mid">Mid-Level</option>
                <option value="Senior">Senior</option>
                <option value="Lead">Lead / Staff</option>
                <option value="Executive">Executive</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Job Category
              </label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white border border-white/10"
              >
                <option value="Engineering">Engineering</option>
                <option value="Design">Design</option>
                <option value="Product">Product</option>
                <option value="Data & AI">Data & AI</option>
                <option value="Marketing">Marketing</option>
                <option value="Sales">Sales</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Posting Status
              </label>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value as JobStatus)}
                className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white border border-white/10"
              >
                <option value="active">Active (Visible)</option>
                <option value="draft">Draft</option>
                <option value="closed">Closed</option>
              </select>
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Full Role Description *
            </label>
            <textarea
              rows={5}
              required
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Detail the scope of the team, mission, and day-to-day expectations..."
              className="w-full p-4 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10 leading-relaxed"
            />
          </div>
        </div>

        {/* Experience & Compensation */}
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-5">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <DollarSign className="w-4 h-4 text-emerald-400" />
            <span>Experience & Compensation</span>
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Experience Range (Years): {experienceMin} - {experienceMax} yrs
              </label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min={0}
                  max={20}
                  value={experienceMin}
                  onChange={(e) => setExperienceMin(Number(e.target.value))}
                  className="w-full accent-violet-500"
                />
                <input
                  type="range"
                  min={experienceMin}
                  max={25}
                  value={experienceMax}
                  onChange={(e) => setExperienceMax(Number(e.target.value))}
                  className="w-full accent-blue-500"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Min Salary ($)
                </label>
                <input
                  type="number"
                  value={salaryMin}
                  onChange={(e) => setSalaryMin(e.target.value)}
                  placeholder="80000"
                  className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white border border-white/10"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Max Salary ($)
                </label>
                <input
                  type="number"
                  value={salaryMax}
                  onChange={(e) => setSalaryMax(e.target.value)}
                  placeholder="140000"
                  className="w-full px-4 py-3 rounded-xl glass-input text-sm text-white border border-white/10"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Skills Requirements (Tag inputs) */}
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-5">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-violet-400" />
            <span>Target Capabilities & Competencies</span>
          </h2>

          {/* Required Skills */}
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Required Skills (Type and press Enter)
            </label>
            <input
              type="text"
              value={newSkillInput}
              onChange={(e) => setNewSkillInput(e.target.value)}
              onKeyDown={handleAddSkill}
              placeholder="e.g. PyTorch, React, Kubernetes (Press Enter to add)"
              className="w-full px-4 py-2.5 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10 mb-3"
            />
            <div className="flex flex-wrap gap-2">
              {requiredSkills.map((skill) => (
                <SkillTag
                  key={skill}
                  name={skill}
                  variant="violet"
                  onRemove={() => setRequiredSkills(requiredSkills.filter((s) => s !== skill))}
                />
              ))}
            </div>
          </div>

          {/* Preferred Skills */}
          <div className="pt-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Preferred / Nice-to-Have Skills
            </label>
            <input
              type="text"
              value={newPreferredInput}
              onChange={(e) => setNewPreferredInput(e.target.value)}
              onKeyDown={handleAddPreferred}
              placeholder="e.g. GraphQL, AWS, Terraform (Press Enter)"
              className="w-full px-4 py-2.5 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10 mb-3"
            />
            <div className="flex flex-wrap gap-2">
              {preferredSkills.map((skill) => (
                <SkillTag
                  key={skill}
                  name={skill}
                  variant="default"
                  onRemove={() => setPreferredSkills(preferredSkills.filter((s) => s !== skill))}
                />
              ))}
            </div>
          </div>

          {/* Education Requirements */}
          <div className="pt-2">
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
              Education Requirements (Type and press Enter)
            </label>
            <input
              type="text"
              value={newEduInput}
              onChange={(e) => setNewEduInput(e.target.value)}
              onKeyDown={handleAddEdu}
              placeholder="e.g. Bachelor's in CS, Master's preferred (Press Enter)"
              className="w-full px-4 py-2.5 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10 mb-3"
            />
            <div className="flex flex-wrap gap-2">
              {educationReqs.map((edu) => (
                <SkillTag
                  key={edu}
                  name={edu}
                  variant="default"
                  onRemove={() => setEducationReqs(educationReqs.filter((e) => e !== edu))}
                />
              ))}
            </div>
          </div>
        </div>

        {/* Responsibilities list input */}
        <div className="glass-panel p-6 sm:p-8 rounded-3xl border border-white/10 shadow-xl space-y-5">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-400" />
            <span>Responsibilities Checklist</span>
          </h2>

          <div className="flex gap-2">
            <input
              type="text"
              value={newRespInput}
              onChange={(e) => setNewRespInput(e.target.value)}
              placeholder="Add key responsibility item..."
              className="flex-1 px-4 py-2.5 rounded-xl glass-input text-sm text-white border border-white/10"
            />
            <button
              type="button"
              onClick={handleAddResp}
              className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold cursor-pointer"
            >
              Add Item
            </button>
          </div>

          <ul className="space-y-2">
            {responsibilities.map((resp, i) => (
              <li
                key={i}
                className="flex items-center justify-between gap-3 p-3 rounded-xl bg-white/[0.02] border border-white/5 text-xs text-slate-300"
              >
                <span>{resp}</span>
                <button
                  type="button"
                  onClick={() => setResponsibilities(responsibilities.filter((_, idx) => idx !== i))}
                  className="text-slate-500 hover:text-rose-400 p-1"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Submit */}
        <div className="flex items-center justify-end gap-4 pt-4">
          <button
            type="button"
            onClick={() => navigate('/recruiter/jobs')}
            className="px-6 py-3 rounded-xl text-sm font-semibold text-slate-400 hover:text-white"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="px-8 py-3.5 rounded-xl bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold text-sm shadow-xl shadow-violet-600/30 transition-all flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Publishing Requisition...</span>
              </>
            ) : (
              <>
                <span>Publish Requisition</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
