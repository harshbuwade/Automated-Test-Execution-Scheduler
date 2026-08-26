import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Clock,
  Code2,
  Copy,
  FileText,
  Terminal,
  XCircle,
} from 'lucide-react';
import { executionService } from '../services/executionService';
import type { ExecutionDetail } from '../types/execution';

export const ExecutionDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const executionId = id ? parseInt(id) : 0;

  const [detail, setDetail] = useState<ExecutionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'stdout' | 'stderr'>('stdout');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (executionId) {
      executionService
        .getExecutionById(executionId)
        .then((res) => setDetail(res))
        .catch((err) => console.error('Failed to fetch execution detail:', err))
        .finally(() => setLoading(false));
    }
  }, [executionId]);

  const handleCopyLogs = (text?: string | null) => {
    if (text) {
      navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'passed':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"><CheckCircle2 className="w-3.5 h-3.5 mr-1.5" /> PASSED</span>;
      case 'failed':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/20"><XCircle className="w-3.5 h-3.5 mr-1.5" /> FAILED</span>;
      case 'timeout':
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/20"><AlertTriangle className="w-3.5 h-3.5 mr-1.5" /> TIMEOUT</span>;
      default:
        return <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-bold bg-slate-800 text-slate-400 border border-slate-700">{status}</span>;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="flex flex-col items-center space-y-3">
          <div className="w-8 h-8 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-400 font-medium">Fetching execution telemetry & log streams...</p>
        </div>
      </div>
    );
  }

  if (!detail) {
    return (
      <div className="p-8 text-center bg-slate-900 border border-slate-800 rounded-2xl max-w-md mx-auto space-y-4">
        <AlertTriangle className="w-12 h-12 text-amber-400 mx-auto" />
        <h3 className="text-lg font-bold text-slate-200">Execution Record Not Found</h3>
        <p className="text-xs text-slate-400">The requested execution record does not exist or belongs to another user.</p>
        <Link to="/executions" className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-800 text-slate-200 rounded-xl text-xs font-semibold">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Execution History</span>
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link to="/executions" className="inline-flex items-center space-x-2 text-xs font-semibold text-slate-400 hover:text-cyan-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Back to History</span>
        </Link>

        <div className="flex items-center space-x-3">
          {getStatusBadge(detail.status)}
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800/80 p-6 rounded-2xl space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-4">
          <div>
            <span className="text-xs font-mono text-cyan-400 uppercase tracking-wider">Execution Run #{detail.id}</span>
            <h2 className="text-2xl font-bold text-slate-100 tracking-tight mt-0.5">{detail.test_name || `Test #${detail.test_id}`}</h2>
          </div>

          <div className="flex items-center space-x-2 text-xs text-slate-400 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800">
            <Code2 className="w-4 h-4 text-cyan-400" />
            <span>Framework: <strong className="text-slate-200 capitalize">{detail.test_framework || 'pytest'}</strong></span>
          </div>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <div className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-xl">
            <span className="text-xs text-slate-500 font-medium block">Trigger Type</span>
            <span className="text-sm font-semibold text-slate-200 capitalize">{detail.trigger_type}</span>
          </div>

          <div className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-xl">
            <span className="text-xs text-slate-500 font-medium block">Duration</span>
            <span className="text-sm font-semibold text-indigo-400">{detail.duration ? `${detail.duration} seconds` : '-'}</span>
          </div>

          <div className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-xl">
            <span className="text-xs text-slate-500 font-medium block">Exit Code</span>
            <span className="text-sm font-mono font-bold text-slate-200">{detail.exit_code ?? '-'}</span>
          </div>

          <div className="p-3.5 bg-slate-950/60 border border-slate-800/80 rounded-xl">
            <span className="text-xs text-slate-500 font-medium block">Schedule Expr</span>
            <span className="text-sm font-mono text-cyan-400">{detail.schedule_expression || 'None (Manual)'}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-400 border-t border-slate-800 pt-4">
          <div className="flex items-center space-x-2">
            <Clock className="w-4 h-4 text-slate-500" />
            <span>Started At: <strong className="text-slate-200">{detail.started_at ? new Date(detail.started_at).toLocaleString() : 'N/A'}</strong></span>
          </div>

          <div className="flex items-center space-x-2">
            <Calendar className="w-4 h-4 text-slate-500" />
            <span>Finished At: <strong className="text-slate-200">{detail.finished_at ? new Date(detail.finished_at).toLocaleString() : 'N/A'}</strong></span>
          </div>
        </div>
      </div>

      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden">
        <div className="bg-slate-900 border-b border-slate-800 px-4 py-2.5 flex items-center justify-between">
          <div className="flex space-x-2">
            <button
              onClick={() => setActiveTab('stdout')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'stdout'
                  ? 'bg-slate-800 text-cyan-400 border border-cyan-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Terminal className="w-3.5 h-3.5" />
              <span>Standard Output (stdout)</span>
            </button>

            <button
              onClick={() => setActiveTab('stderr')}
              className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'stderr'
                  ? 'bg-slate-800 text-rose-400 border border-rose-500/30'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Standard Error (stderr)</span>
            </button>
          </div>

          <button
            onClick={() => handleCopyLogs(activeTab === 'stdout' ? detail.stdout : detail.stderr)}
            className="flex items-center space-x-1.5 px-3 py-1.5 bg-slate-950 border border-slate-800 hover:border-slate-700 text-slate-300 rounded-lg text-xs font-semibold transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>{copied ? 'Copied!' : 'Copy Logs'}</span>
          </button>
        </div>

        <div className="p-4 bg-slate-950">
          <pre className="font-mono text-xs text-slate-300 leading-relaxed overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap selection:bg-cyan-500 selection:text-white">
            {activeTab === 'stdout'
              ? detail.stdout || '// No stdout logs recorded for this execution.'
              : detail.stderr || '// No stderr logs recorded for this execution.'}
          </pre>
        </div>
      </div>
    </div>
  );
};
