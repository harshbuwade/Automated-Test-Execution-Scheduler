import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  Filter,
  RefreshCw,
  XCircle,
} from 'lucide-react';
import { executionService } from '../services/executionService';
import { testService } from '../services/testService';
import type { ExecutionSummary } from '../types/execution';
import type { TestItem } from '../types/test';

export const ExecutionsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();

  const initialScheduleId = searchParams.get('schedule_id') ? parseInt(searchParams.get('schedule_id')!) : undefined;
  const initialTestId = searchParams.get('test_id') ? parseInt(searchParams.get('test_id')!) : undefined;

  const [executions, setExecutions] = useState<ExecutionSummary[]>([]);
  const [availableTests, setAvailableTests] = useState<TestItem[]>([]);
  const [loading, setLoading] = useState(true);

  const [selectedTestId, setSelectedTestId] = useState<number | undefined>(initialTestId);
  const [selectedScheduleId, setSelectedScheduleId] = useState<number | undefined>(initialScheduleId);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [triggerFilter, setTriggerFilter] = useState<string>('');
  const [dateFrom, setDateFrom] = useState<string>('');
  const [dateTo, setDateTo] = useState<string>('');

  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);

  const fetchExecutions = async () => {
    try {
      setLoading(true);
      const res = await executionService.getExecutions(
        page,
        10,
        selectedTestId,
        selectedScheduleId,
        statusFilter || undefined,
        triggerFilter || undefined,
        dateFrom ? new Date(dateFrom).toISOString() : undefined,
        dateTo ? new Date(dateTo).toISOString() : undefined
      );
      setExecutions(res.items);
      setTotal(res.total);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to fetch execution history:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    testService.getTests(1, 100).then((res) => setAvailableTests(res.items)).catch(() => {});
  }, []);

  useEffect(() => {
    fetchExecutions();
  }, [page, selectedTestId, selectedScheduleId, statusFilter, triggerFilter, dateFrom, dateTo]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'passed':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle2 className="w-3 h-3 mr-1" /> Passed</span>;
      case 'failed':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20"><XCircle className="w-3 h-3 mr-1" /> Failed</span>;
      case 'timeout':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20"><AlertTriangle className="w-3 h-3 mr-1" /> Timeout</span>;
      case 'running':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse"><RefreshCw className="w-3 h-3 mr-1 animate-spin" /> Running</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">{status}</span>;
    }
  };

  const handleResetFilters = () => {
    setSelectedTestId(undefined);
    setSelectedScheduleId(undefined);
    setStatusFilter('');
    setTriggerFilter('');
    setDateFrom('');
    setDateTo('');
    setSearchParams({});
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Execution History & Logs</h2>
          <p className="text-xs text-slate-400">Complete audit trail of manual and scheduled test runs ({total} total records).</p>
        </div>

        <button
          onClick={fetchExecutions}
          className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-all self-start"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh</span>
        </button>
      </div>

      <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl space-y-3">
        <div className="flex items-center justify-between text-xs font-semibold text-slate-400 uppercase tracking-wider">
          <span className="flex items-center space-x-1.5">
            <Filter className="w-3.5 h-3.5 text-cyan-400" />
            <span>Filter Execution Logs</span>
          </span>
          <button onClick={handleResetFilters} className="text-cyan-400 hover:underline">
            Reset Filters
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Test Script</label>
            <select
              value={selectedTestId || ''}
              onChange={(e) => {
                setSelectedTestId(e.target.value ? parseInt(e.target.value) : undefined);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Test Scripts</option>
              {availableTests.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Status</label>
            <select
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Statuses</option>
              <option value="passed">Passed</option>
              <option value="failed">Failed</option>
              <option value="timeout">Timeout</option>
              <option value="running">Running</option>
              <option value="pending">Pending</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">Trigger Type</label>
            <select
              value={triggerFilter}
              onChange={(e) => {
                setTriggerFilter(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            >
              <option value="">All Triggers</option>
              <option value="manual">Manual</option>
              <option value="scheduled">Scheduled</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">From Date</label>
            <input
              type="date"
              value={dateFrom}
              onChange={(e) => {
                setDateFrom(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">To Date</label>
            <input
              type="date"
              value={dateTo}
              onChange={(e) => {
                setDateTo(e.target.value);
                setPage(1);
              }}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
            />
          </div>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase bg-slate-900/80">
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Test</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Trigger</th>
                <th className="py-3 px-4">Duration</th>
                <th className="py-3 px-4">Exit Code</th>
                <th className="py-3 px-4">Started At</th>
                <th className="py-3 px-4 text-right">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <div className="inline-block w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                  </td>
                </tr>
              ) : executions.length > 0 ? (
                executions.map((e) => (
                  <tr key={e.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-mono text-xs text-cyan-400">#{e.id}</td>
                    <td className="py-3.5 px-4 text-slate-200 font-medium">Test #{e.test_id}</td>
                    <td className="py-3.5 px-4">{getStatusBadge(e.status)}</td>
                    <td className="py-3.5 px-4 capitalize text-xs text-slate-300">
                      {e.trigger_type} {e.schedule_id ? `(Sched #${e.schedule_id})` : ''}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-300">{e.duration ? `${e.duration}s` : '-'}</td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-300">{e.exit_code ?? '-'}</td>
                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {e.started_at ? new Date(e.started_at).toLocaleString() : new Date(e.created_at).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/executions/${e.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-semibold transition-colors"
                      >
                        <span>View Logs</span>
                        <ExternalLink className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    No execution logs match the selected filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {totalPages > 1 && (
          <div className="p-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
            <span>Page {page} of {totalPages}</span>
            <div className="flex space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg disabled:opacity-50"
              >
                Previous
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => setPage(page + 1)}
                className="px-3 py-1.5 bg-slate-900 border border-slate-800 rounded-lg disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
