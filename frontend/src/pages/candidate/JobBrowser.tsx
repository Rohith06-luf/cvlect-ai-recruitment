import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Search,
  MapPin,
  DollarSign,
  Bookmark,
  BookmarkCheck,
  Filter,
  ChevronLeft,
  ChevronRight,
  ArrowRight,
} from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../components/ui/Toast';
import { SkillTag } from '../../components/ui/SkillTag';
import { CardSkeleton } from '../../components/ui/LoadingSkeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import type { JobResponse } from '../../types';

export const JobBrowser: React.FC = () => {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [savedJobIds, setSavedJobIds] = useState<Set<number>>(new Set());
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [selectedWorkMode, setSelectedWorkMode] = useState<string>('all');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalJobs, setTotalJobs] = useState(0);

  const toast = useToast();

  const fetchJobs = async () => {
    setIsLoading(true);
    try {
      const [jobsData, savedList] = await Promise.allSettled([
        api.jobs.list({
          page,
          per_page: 9,
          search: search.trim() || undefined,
          work_mode: selectedWorkMode !== 'all' ? selectedWorkMode : undefined,
          category: selectedCategory !== 'all' ? selectedCategory : undefined,
        }),
        api.savedJobs.list(),
      ]);

      if (jobsData.status === 'fulfilled') {
        setJobs(jobsData.value.items);
        setTotalPages(jobsData.value.pages);
        setTotalJobs(jobsData.value.total);
      }
      if (savedList.status === 'fulfilled') {
        const idSet = new Set(savedList.value.map((s) => s.job_id));
        setSavedJobIds(idSet);
      }
    } catch (err) {
      console.error('Failed to fetch jobs', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [page, selectedWorkMode, selectedCategory]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchJobs();
  };

  const toggleSaveJob = async (e: React.MouseEvent, jobId: number) => {
    e.preventDefault();
    e.stopPropagation();

    const isCurrentlySaved = savedJobIds.has(jobId);
    try {
      if (isCurrentlySaved) {
        await api.savedJobs.unsave(jobId);
        setSavedJobIds((prev) => {
          const next = new Set(prev);
          next.delete(jobId);
          return next;
        });
        toast.info('Job Removed', 'Removed from your saved bookmarks.');
      } else {
        await api.savedJobs.save(jobId);
        setSavedJobIds((prev) => new Set(prev).add(jobId));
        toast.success('Job Saved', 'Added to your bookmarked positions.');
      }
    } catch {
      toast.error('Error', 'Could not update bookmark.');
    }
  };

  const categories = ['Engineering', 'Design', 'Product', 'Data & AI', 'Marketing', 'Sales'];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Smart Job Explorer</h1>
        <p className="mt-1 text-sm text-slate-300">
          Explore AI-indexed job requisitions ranked with multi-factor profile compatibility.
        </p>
      </div>

      {/* Filter and Search Bar */}
      <div className="glass-panel p-5 rounded-3xl border border-white/10 shadow-xl space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by title, keywords, or company..."
              className="w-full pl-10 pr-4 py-3 rounded-xl glass-input text-sm text-white placeholder-slate-400 border border-white/10"
            />
          </div>
          <button
            type="submit"
            className="px-6 py-3 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-semibold text-sm shadow-md transition-all cursor-pointer"
          >
            Search
          </button>
        </form>

        {/* Filter Pills */}
        <div className="flex flex-wrap items-center justify-between gap-4 pt-2 border-t border-white/5 text-xs">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-slate-400 font-medium mr-1 flex items-center gap-1">
              <Filter className="w-3.5 h-3.5" />
              Work Mode:
            </span>
            {['all', 'remote', 'hybrid', 'onsite'].map((mode) => (
              <button
                key={mode}
                onClick={() => {
                  setSelectedWorkMode(mode);
                  setPage(1);
                }}
                className={`px-3 py-1.5 rounded-lg capitalize font-medium transition-colors ${
                  selectedWorkMode === mode
                    ? 'bg-violet-600 text-white shadow-sm'
                    : 'bg-white/5 text-slate-400 hover:text-white'
                }`}
              >
                {mode}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-slate-400 font-medium">Category:</span>
            <select
              value={selectedCategory}
              onChange={(e) => {
                setSelectedCategory(e.target.value);
                setPage(1);
              }}
              className="px-3 py-1.5 rounded-lg glass-input text-xs text-white border border-white/10"
            >
              <option value="all">All Categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Job Cards Grid */}
      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 6 }).map((_, i) => (
            <CardSkeleton key={i} />
          ))}
        </div>
      ) : jobs.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {jobs.map((job) => {
            const isSaved = savedJobIds.has(job.id);
            return (
              <motion.div
                key={job.id}
                whileHover={{ y: -4 }}
                transition={{ duration: 0.2 }}
                className="group relative rounded-3xl glass-panel border border-white/10 hover:border-violet-500/40 p-6 flex flex-col justify-between shadow-xl transition-all"
              >
                <div>
                  {/* Top Bar: Company & Bookmark */}
                  <div className="flex items-start justify-between gap-2 mb-3">
                    <span className="text-xs font-semibold text-violet-400 uppercase tracking-wider">
                      {job.company}
                    </span>
                    <button
                      onClick={(e) => toggleSaveJob(e, job.id)}
                      className={`p-2 rounded-xl border transition-colors cursor-pointer ${
                        isSaved
                          ? 'bg-violet-600/20 border-violet-500/40 text-violet-400'
                          : 'bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/10'
                      }`}
                      title={isSaved ? 'Remove bookmark' : 'Bookmark job'}
                    >
                      {isSaved ? <BookmarkCheck className="w-4 h-4" /> : <Bookmark className="w-4 h-4" />}
                    </button>
                  </div>

                  {/* Title */}
                  <Link
                    to={`/candidate/jobs/${job.id}`}
                    className="text-lg font-bold text-white group-hover:text-violet-300 transition-colors line-clamp-1 mb-2 block"
                  >
                    {job.title}
                  </Link>

                  {/* Location & Mode */}
                  <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400 mb-4">
                    <span className="flex items-center gap-1">
                      <MapPin className="w-3.5 h-3.5 text-slate-500" />
                      {job.location || 'Remote'}
                    </span>
                    <span className="capitalize px-2 py-0.5 rounded-full bg-slate-800 text-slate-300 border border-white/5 font-medium">
                      {job.work_mode}
                    </span>
                    {job.salary_min && (
                      <span className="flex items-center gap-0.5 text-emerald-400 font-semibold">
                        <DollarSign className="w-3.5 h-3.5" />
                        {(job.salary_min / 1000).toFixed(0)}k - {(job.salary_max ? job.salary_max / 1000 : 0).toFixed(0)}k
                      </span>
                    )}
                  </div>

                  {/* Description snippet */}
                  <p className="text-xs text-slate-400 line-clamp-3 mb-4 leading-relaxed">
                    {job.description}
                  </p>

                  {/* Skills tags */}
                  {job.required_skills && job.required_skills.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mb-6">
                      {job.required_skills.slice(0, 4).map((skill) => (
                        <SkillTag key={skill} name={skill} variant="default" size="sm" />
                      ))}
                      {job.required_skills.length > 4 && (
                        <span className="text-[10px] text-slate-400 self-center">
                          +{job.required_skills.length - 4} more
                        </span>
                      )}
                    </div>
                  )}
                </div>

                {/* Footer Link */}
                <div className="pt-4 border-t border-white/5 flex items-center justify-between">
                  <span className="text-[11px] text-slate-400">
                    Exp: {job.experience_min} - {job.experience_max} yrs
                  </span>
                  <Link
                    to={`/candidate/jobs/${job.id}`}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-violet-400 hover:text-violet-300 group-hover:translate-x-1 transition-transform"
                  >
                    <span>View Requisition</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </motion.div>
            );
          })}
        </div>
      ) : (
        <EmptyState
          title="No jobs found"
          description="Try modifying your search criteria or resetting the work mode filter."
          actionLabel="Clear Filters"
          onAction={() => {
            setSearch('');
            setSelectedWorkMode('all');
            setSelectedCategory('all');
            setPage(1);
          }}
        />
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-6 border-t border-white/10 text-xs text-slate-400">
          <span>
            Showing <strong className="text-white">{jobs.length}</strong> of{' '}
            <strong className="text-white">{totalJobs}</strong> positions
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="p-2 rounded-xl glass-panel border border-white/10 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed text-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="px-3 py-1 font-semibold text-white">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="p-2 rounded-xl glass-panel border border-white/10 hover:bg-white/5 disabled:opacity-30 disabled:cursor-not-allowed text-white"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
