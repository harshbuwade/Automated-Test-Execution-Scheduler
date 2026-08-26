import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Activity,
  AlertTriangle,
  ArrowUpRight,
  Calendar,
  CheckCircle2,
  Clock,
  ExternalLink,
  PlaySquare,
  RefreshCw,
  TrendingUp,
  XCircle,
} from 'lucide-react';
import { Bar, BarChart, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { executionService } from '../services/executionService';
import { scheduleService } from '../services/scheduleService';
import type { ExecutionStats, ExecutionSummary } from '../types/execution';
import type { ScheduleItem } from '../types/schedule';

export const DashboardPage: React.FC = () => {
  const [stats, setStats] = useState<ExecutionStats | null>(null);
  const [recentExecutions, setRecentExecutions] = useState<ExecutionSummary[]>([]);
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      setRefreshing(true);
      const [statsData, recentData, schedulesData] = await Promise.all([
        executionService.getExecutionStats(),
        executionService.getRecentExecutions(7),
        scheduleService.getSchedules(1, 5, undefined, true),
      ]);
      setStats(statsData);
      setRecentExecutions(recentData);
      setSchedules(schedulesData.items);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'passed':
        return <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle2 className="w-3 h-3 mr-1" /> Passed</span>;
      case 'failed':
        return <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20"><XCircle className="w-3 h-3 mr-1" /> Failed</span>;
      case 'timeout':
        return <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20"><AlertTriangle className="w-3 h-3 mr-1" /> Timeout</span>;
      case 'running':
        return <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-blue-500/10 text-blue-400 border border-blue-500/20 animate-pulse"><RefreshCw className="w-3 h-3 mr-1 animate-spin" /> Running</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">{status}</span>;
    }
  };

  const pieData = stats
    ? [
        { name: 'Passed', value: stats.passed, color: '#10b981' },
        { name: 'Failed', value: stats.failed, color: '#f43f5e' },
        { name: 'Timeout', value: stats.timeout, color: '#f59e0b' },
        { name: 'Pending/Running', value: stats.pending + stats.running, color: '#3b82f6' },
      ].filter((item) => item.value > 0)
    : [];

  const chartBarData = recentExecutions
    .slice()
    .reverse()
    .map((e) => ({
      name: `Run #${e.id}`,
      duration: e.duration || 0,
      status: e.status,
    }));

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-400 font-medium">Loading dashboard telemetry...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">System Telemetry & Overview</h2>
          <p className="text-xs text-slate-400">Real-time metrics, execution distributions, and active schedules.</p>
        </div>
        <button
          onClick={fetchData}
          disabled={refreshing}
          className="flex items-center space-x-2 px-3.5 py-2 bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-xl text-xs font-semibold transition-all"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${refreshing ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Total Runs</span>
            <PlaySquare className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-slate-100">{stats?.total_executions || 0}</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Passed</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          </div>
          <p className="text-2xl font-bold text-emerald-400">{stats?.passed || 0}</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Failed</span>
            <XCircle className="w-4 h-4 text-rose-400" />
          </div>
          <p className="text-2xl font-bold text-rose-400">{stats?.failed || 0}</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Timeout</span>
            <AlertTriangle className="w-4 h-4 text-amber-400" />
          </div>
          <p className="text-2xl font-bold text-amber-400">{stats?.timeout || 0}</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Success Rate</span>
            <TrendingUp className="w-4 h-4 text-cyan-400" />
          </div>
          <p className="text-2xl font-bold text-cyan-400">{stats?.success_rate ? `${stats.success_rate}%` : '0%'}</p>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-4 rounded-2xl">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-semibold uppercase">Avg Duration</span>
            <Clock className="w-4 h-4 text-indigo-400" />
          </div>
          <p className="text-2xl font-bold text-indigo-400">{stats?.average_duration ? `${stats.average_duration}s` : '0s'}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl">
          <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center space-x-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <span>Execution Status Distribution</span>
          </h3>

          {pieData.length > 0 ? (
            <div className="h-64 flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={55}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', color: '#f8fafc' }}
                  />
                </PieChart>
              </ResponsiveContainer>
              <div className="ml-4 space-y-2">
                {pieData.map((item) => (
                  <div key={item.name} className="flex items-center space-x-2 text-xs">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <span className="text-slate-300 font-medium">{item.name}:</span>
                    <span className="text-slate-100 font-bold">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
              No execution status metrics recorded yet.
            </div>
          )}
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 p-5 rounded-2xl">
          <h3 className="text-sm font-semibold text-slate-200 mb-4 flex items-center space-x-2">
            <Clock className="w-4 h-4 text-indigo-400" />
            <span>Recent Run Durations (Seconds)</span>
          </h3>

          {chartBarData.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartBarData}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '0.75rem', color: '#f8fafc' }}
                  />
                  <Bar dataKey="duration" fill="#6366f1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-slate-500 text-sm">
              No recent execution durations available.
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
              <PlaySquare className="w-4 h-4 text-cyan-400" />
              <span>Recent Executions</span>
            </h3>
            <Link to="/executions" className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center space-x-1">
              <span>View All</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase">
                  <th className="py-2.5 px-3">Run ID</th>
                  <th className="py-2.5 px-3">Test ID</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Trigger</th>
                  <th className="py-2.5 px-3">Duration</th>
                  <th className="py-2.5 px-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {recentExecutions.length > 0 ? (
                  recentExecutions.map((e) => (
                    <tr key={e.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="py-3 px-3 font-mono text-xs text-slate-300">#{e.id}</td>
                      <td className="py-3 px-3 text-slate-200 font-medium">Test #{e.test_id}</td>
                      <td className="py-3 px-3">{getStatusBadge(e.status)}</td>
                      <td className="py-3 px-3 capitalize text-xs text-slate-400">{e.trigger_type}</td>
                      <td className="py-3 px-3 text-xs text-slate-300">{e.duration ? `${e.duration}s` : '-'}</td>
                      <td className="py-3 px-3">
                        <Link
                          to={`/executions/${e.id}`}
                          className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-cyan-400 inline-flex items-center transition-colors"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-500 text-sm">
                      No executions recorded yet.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-200 flex items-center space-x-2">
              <Calendar className="w-4 h-4 text-cyan-400" />
              <span>Upcoming Schedules</span>
            </h3>
            <Link to="/schedules" className="text-xs font-semibold text-cyan-400 hover:text-cyan-300 flex items-center space-x-1">
              <span>Manage</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="space-y-3">
            {schedules.length > 0 ? (
              schedules.map((s) => (
                <div key={s.id} className="p-3.5 bg-slate-950/60 border border-slate-800 rounded-xl space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-200">Test #{s.test_id}</span>
                    <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                      {s.schedule_type}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-xs text-slate-400">
                    <span>Expr: <code className="text-slate-200 bg-slate-800 px-1 py-0.5 rounded">{s.schedule_expression}</code></span>
                    <span className="text-[11px] text-slate-500">
                      Next: {s.next_run ? new Date(s.next_run).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Paused'}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-slate-500 text-sm">
                No active schedules configured.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
