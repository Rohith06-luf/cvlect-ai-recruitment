import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  PlusCircle,
  Users,
  Trash2,
} from 'lucide-react';
import { api } from '../../api/client';
import { useToast } from '../../components/ui/Toast';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { Modal } from '../../components/ui/Modal';
import { TableSkeleton } from '../../components/ui/LoadingSkeleton';
import { EmptyState } from '../../components/ui/EmptyState';
import type { JobResponse, JobStatus } from '../../types';

export const JobManagement: React.FC = () => {
  const [jobs, setJobs] = useState<JobResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [deletingJobId, setDeletingJobId] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const navigate = useNavigate();
  const toast = useToast();

  const fetchJobs = async () => {
    setIsLoading(true);
    try {
      const data = await api.jobs.list({ per_page: 50 });
      setJobs(data.items);
    } catch (err) {
      toast.error('Error', 'Failed to retrieve job listings.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleStatusChange = async (jobId: number, newStatus: JobStatus) => {
    try {
      await api.jobs.update(jobId, { status: newStatus });
      setJobs((prev) =>
        prev.map((j) => (j.id === jobId ? { ...j, status: newStatus } : j))
      );
      toast.success('Status Updated', `Position status changed to ${newStatus}.`);
    } catch {
      toast.error('Error', 'Failed to update position status.');
    }
  };

  const confirmDelete = async () => {
    if (!deletingJobId) return;
    setIsDeleting(true);
    try {
      await api.jobs.delete(deletingJobId);
      setJobs((prev) => prev.filter((j) => j.id !== deletingJobId));
      toast.success('Requisition Deleted', 'The job has been removed successfully.');
      setDeletingJobId(null);
    } catch {
      toast.error('Error', 'Could not delete job.');
    } finally {
      setIsDeleting(false);
    }
  };

  const columns: Column<JobResponse>[] = [
    {
      key: 'title',
      header: 'Position Title',
      sortable: true,
      render: (job) => (
        <div>
          <span className="font-bold text-white text-sm block">{job.title}</span>
          <span className="text-xs text-slate-400">
            {job.company} • {job.location || 'Remote'}
          </span>
        </div>
      ),
    },
    {
      key: 'work_mode',
      header: 'Work Mode',
      sortable: true,
      render: (job) => (
        <span className="capitalize text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-800 text-slate-300 border border-white/5">
          {job.work_mode}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (job) => (
        <select
          value={job.status}
          onChange={(e) => handleStatusChange(job.id, e.target.value as JobStatus)}
          className={`text-xs font-semibold px-2.5 py-1 rounded-xl border appearance-none cursor-pointer bg-slate-900 ${
            job.status === 'active'
              ? 'border-emerald-500/40 text-emerald-400'
              : job.status === 'closed'
              ? 'border-rose-500/40 text-rose-400'
              : 'border-amber-500/40 text-amber-400'
          }`}
        >
          <option value="active">Active</option>
          <option value="draft">Draft</option>
          <option value="closed">Closed</option>
        </select>
      ),
    },
    {
      key: 'experience',
      header: 'Experience',
      render: (job) => (
        <span className="text-xs text-slate-300">
          {job.experience_min} - {job.experience_max} yrs
        </span>
      ),
    },
    {
      key: 'created_at',
      header: 'Posted Date',
      sortable: true,
      render: (job) => (
        <span className="text-xs text-slate-400">
          {new Date(job.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (job) => (
        <div className="flex items-center gap-2">
          <Link
            to={`/recruiter/candidates?job_id=${job.id}`}
            className="p-1.5 rounded-lg bg-violet-600/20 text-violet-400 hover:bg-violet-600 hover:text-white transition-colors"
            title="Rank Candidates"
          >
            <Users className="w-4 h-4" />
          </Link>
          <button
            onClick={() => setDeletingJobId(job.id)}
            className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:bg-rose-500/20 hover:text-rose-400 transition-colors cursor-pointer"
            title="Delete Requisition"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Job Requisition Management</h1>
          <p className="mt-1 text-sm text-slate-300">
            Publish, edit, and supervise active talent requisitions.
          </p>
        </div>

        <Link
          to="/recruiter/jobs/create"
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-semibold text-xs sm:text-sm shadow-lg shadow-violet-600/30 transition-all flex items-center justify-center gap-2"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Post New Job</span>
        </Link>
      </div>

      {/* Content */}
      {isLoading ? (
        <TableSkeleton rows={6} />
      ) : jobs.length > 0 ? (
        <DataTable
          data={jobs}
          columns={columns}
          searchKey="title"
          searchPlaceholder="Search jobs by title or company..."
          pageSize={10}
        />
      ) : (
        <EmptyState
          title="No Job Postings Yet"
          description="Create your first job requisition to start matching with candidates."
          actionLabel="Create Job"
          onAction={() => navigate('/recruiter/jobs/create')}
        />
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={deletingJobId !== null}
        onClose={() => setDeletingJobId(null)}
        title="Delete Requisition"
        subtitle="This action cannot be undone. All candidate rankings for this job will be removed."
        maxWidth="sm"
        footer={
          <>
            <button
              onClick={() => setDeletingJobId(null)}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-400 hover:text-white"
            >
              Cancel
            </button>
            <button
              onClick={confirmDelete}
              disabled={isDeleting}
              className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold transition-colors cursor-pointer"
            >
              {isDeleting ? 'Deleting...' : 'Confirm Delete'}
            </button>
          </>
        }
      >
        <p className="text-xs text-slate-300">
          Are you sure you wish to permanently delete this requisition?
        </p>
      </Modal>
    </div>
  );
};
