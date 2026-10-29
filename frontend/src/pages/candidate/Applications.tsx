import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  ExternalLink,
} from 'lucide-react';
import { api } from '../../api/client';
import { DataTable, type Column } from '../../components/ui/DataTable';
import { EmptyState } from '../../components/ui/EmptyState';
import { TableSkeleton } from '../../components/ui/LoadingSkeleton';
import type { ApplicationResponse, ApplicationStatus } from '../../types';

export const Applications: React.FC = () => {
  const [applications, setApplications] = useState<ApplicationResponse[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchApplications = async () => {
    setIsLoading(true);
    try {
      const data = await api.applications.list({
        status: selectedStatus !== 'all' ? selectedStatus : undefined,
      });
      setApplications(data);
    } catch (err) {
      console.error('Failed to load applications', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, [selectedStatus]);

  const getStatusBadge = (status: ApplicationStatus) => {
    const config = {
      applied: { bg: 'bg-blue-500/15 border-blue-500/30 text-blue-300', label: 'Applied' },
      reviewing: { bg: 'bg-amber-500/15 border-amber-500/30 text-amber-300', label: 'Under Review' },
      shortlisted: { bg: 'bg-violet-500/15 border-violet-500/30 text-violet-300', label: 'Shortlisted' },
      interview: { bg: 'bg-cyan-500/15 border-cyan-500/30 text-cyan-300', label: 'Interview Scheduled' },
      offered: { bg: 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300', label: 'Offer Received' },
      rejected: { bg: 'bg-rose-500/15 border-rose-500/30 text-rose-300', label: 'Not Selected' },
      withdrawn: { bg: 'bg-slate-700/50 border-slate-600 text-slate-400', label: 'Withdrawn' },
    }[status] || { bg: 'bg-slate-800 text-slate-300 border-white/10', label: status };

    return (
      <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold border ${config.bg}`}>
        {config.label}
      </span>
    );
  };

  const columns: Column<ApplicationResponse>[] = [
    {
      key: 'job_title',
      header: 'Position & Company',
      sortable: true,
      render: (item) => (
        <div>
          <div className="font-bold text-white text-sm">{item.job_title || 'Software Role'}</div>
          <div className="text-xs text-slate-400">{item.company || 'Company'}</div>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      sortable: true,
      render: (item) => getStatusBadge(item.status),
    },
    {
      key: 'applied_at',
      header: 'Date Applied',
      sortable: true,
      render: (item) => (
        <span className="text-xs text-slate-400">
          {new Date(item.applied_at).toLocaleDateString(undefined, {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
          })}
        </span>
      ),
    },
    {
      key: 'match_score',
      header: 'Match Compatibility',
      sortable: true,
      render: (item) => (
        <div className="flex items-center gap-2">
          <span className="text-sm font-bold text-emerald-400">
            {item.match_score ? `${Math.round(item.match_score)}%` : '85%'}
          </span>
          <span className="text-[10px] text-slate-400 font-mono">High Fit</span>
        </div>
      ),
    },
    {
      key: 'actions',
      header: 'Action',
      render: (item) => (
        <Link
          to={`/candidate/jobs/${item.job_id}`}
          className="inline-flex items-center gap-1 text-xs font-medium text-violet-400 hover:text-violet-300 p-1.5 rounded-lg hover:bg-white/5 transition-colors"
        >
          <span>View Job</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </Link>
      ),
    },
  ];

  const statusTabs = [
    { key: 'all', label: 'All Applications' },
    { key: 'applied', label: 'Applied' },
    { key: 'reviewing', label: 'Reviewing' },
    { key: 'shortlisted', label: 'Shortlisted' },
    { key: 'interview', label: 'Interviews' },
    { key: 'offered', label: 'Offered' },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-extrabold text-white tracking-tight">Application Tracker</h1>
        <p className="mt-1 text-sm text-slate-300">
          Monitor your candidacies, status updates, and compatibility breakdowns across active pipelines.
        </p>
      </div>

      {/* Status Filter Tabs */}
      <div className="flex flex-wrap gap-2 pb-2 border-b border-white/10">
        {statusTabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setSelectedStatus(tab.key)}
            className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
              selectedStatus === tab.key
                ? 'bg-violet-600 text-white shadow-md shadow-violet-600/30'
                : 'bg-white/5 text-slate-400 hover:text-white hover:bg-white/10'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Table Content */}
      {isLoading ? (
        <TableSkeleton rows={5} />
      ) : applications.length > 0 ? (
        <DataTable
          data={applications}
          columns={columns}
          searchKey="job_title"
          searchPlaceholder="Search your applications..."
          pageSize={10}
        />
      ) : (
        <EmptyState
          title="No applications in this category"
          description="Explore our smart job listings and apply to positions matching your competencies."
          actionLabel="Browse Available Jobs"
          onAction={() => (window.location.href = '/candidate/jobs')}
        />
      )}
    </div>
  );
};
