import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertCircle,
  Edit2,
  ExternalLink,
  PauseCircle,
  PlayCircle,
  Plus,
  Trash2,
  X,
} from 'lucide-react';
import { scheduleService } from '../services/scheduleService';
import { testService } from '../services/testService';
import type { ScheduleCreate, ScheduleItem, ScheduleType } from '../types/schedule';
import type { TestItem } from '../types/test';

export const SchedulesPage: React.FC = () => {
  const [schedules, setSchedules] = useState<ScheduleItem[]>([]);
  const [availableTests, setAvailableTests] = useState<TestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingSchedule, setEditingSchedule] = useState<ScheduleItem | null>(null);
  const [formData, setFormData] = useState<ScheduleCreate>({
    test_id: 0,
    schedule_type: 'interval',
    schedule_expression: '60',
    is_active: true,
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [schedRes, testRes] = await Promise.all([
        scheduleService.getSchedules(page, 10),
        testService.getTests(1, 100),
      ]);
      setSchedules(schedRes.items);
      setTotalPages(schedRes.total_pages);
      setAvailableTests(testRes.items);
    } catch (err) {
      console.error('Failed to fetch schedules data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [page]);

  const handleOpenCreateModal = () => {
    setEditingSchedule(null);
    setFormData({
      test_id: availableTests.length > 0 ? availableTests[0].id : 0,
      schedule_type: 'interval',
      schedule_expression: '60',
      is_active: true,
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (s: ScheduleItem) => {
    setEditingSchedule(s);
    setFormData({
      test_id: s.test_id,
      schedule_type: s.schedule_type,
      schedule_expression: s.schedule_expression,
      is_active: s.is_active,
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.test_id) {
      setFormError('Please select a test script.');
      return;
    }
    if (!formData.schedule_expression) {
      setFormError('Schedule expression cannot be empty.');
      return;
    }

    try {
      setSubmitting(true);
      if (editingSchedule) {
        await scheduleService.updateSchedule(editingSchedule.id, {
          schedule_type: formData.schedule_type,
          schedule_expression: formData.schedule_expression,
          is_active: formData.is_active,
        });
      } else {
        await scheduleService.createSchedule(formData);
      }
      setIsModalOpen(false);
      fetchData();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to save schedule.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleTogglePauseResume = async (s: ScheduleItem) => {
    try {
      if (s.is_active) {
        await scheduleService.pauseSchedule(s.id);
      } else {
        await scheduleService.resumeSchedule(s.id);
      }
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to toggle schedule active state.');
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this schedule? (Past execution history will be preserved)')) return;

    try {
      await scheduleService.deleteSchedule(id);
      fetchData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete schedule.');
    }
  };

  const getTestName = (testId: number) => {
    const found = availableTests.find((t) => t.id === testId);
    return found ? found.name : `Test #${testId}`;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-slate-100 tracking-tight">Automated Test Schedules</h2>
          <p className="text-xs text-slate-400">Manage interval and cron automated background test execution jobs.</p>
        </div>

        <button
          onClick={handleOpenCreateModal}
          className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold rounded-xl text-sm shadow-lg shadow-cyan-500/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Schedule</span>
        </button>
      </div>

      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase bg-slate-900/80">
                <th className="py-3 px-4">Test</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Expression</th>
                <th className="py-3 px-4">Active</th>
                <th className="py-3 px-4">Next Run</th>
                <th className="py-3 px-4">Last Run</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {loading ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400">
                    <div className="inline-block w-6 h-6 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin"></div>
                  </td>
                </tr>
              ) : schedules.length > 0 ? (
                schedules.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-100">
                      {getTestName(s.test_id)}
                      <span className="block text-xs font-mono text-slate-500 font-normal">ID #{s.test_id}</span>
                    </td>
                    <td className="py-3.5 px-4 uppercase text-xs font-bold text-cyan-400">{s.schedule_type}</td>
                    <td className="py-3.5 px-4 font-mono text-xs text-slate-200">
                      <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800">{s.schedule_expression}</span>
                    </td>
                    <td className="py-3.5 px-4">
                      {s.is_active ? (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                          Active
                        </span>
                      ) : (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                          Paused
                        </span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-300">
                      {s.next_run ? new Date(s.next_run).toLocaleString() : '-'}
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {s.last_run ? new Date(s.last_run).toLocaleString() : 'Never'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleTogglePauseResume(s)}
                          className={`p-1.5 rounded-lg transition-colors ${
                            s.is_active
                              ? 'hover:bg-amber-500/10 text-amber-400'
                              : 'hover:bg-emerald-500/10 text-emerald-400'
                          }`}
                          title={s.is_active ? 'Pause Schedule' : 'Resume Schedule'}
                        >
                          {s.is_active ? <PauseCircle className="w-4 h-4" /> : <PlayCircle className="w-4 h-4" />}
                        </button>

                        <Link
                          to={`/executions?schedule_id=${s.id}`}
                          className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-cyan-400 rounded-lg transition-colors"
                          title="View Schedule Executions"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Link>

                        <button
                          onClick={() => handleOpenEditModal(s)}
                          className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
                          title="Edit Schedule"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleDelete(s.id)}
                          className="p-1.5 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg transition-colors"
                          title="Delete Schedule"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-500">
                    No automated schedules configured. Click "New Schedule" to create one.
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

      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <h3 className="text-lg font-bold text-slate-100">
                {editingSchedule ? 'Edit Schedule' : 'Create Automated Schedule'}
              </h3>
              <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            {formError && (
              <div className="p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl flex items-center space-x-2 text-rose-400 text-xs">
                <AlertCircle className="w-4 h-4 flex-shrink-0" />
                <span>{formError}</span>
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4">
              {!editingSchedule && (
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Target Test Script *</label>
                  <select
                    value={formData.test_id}
                    onChange={(e) => setFormData({ ...formData, test_id: parseInt(e.target.value) })}
                    required
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-cyan-500"
                  >
                    {availableTests.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.script_path})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Schedule Type *</label>
                  <select
                    value={formData.schedule_type}
                    onChange={(e) => setFormData({ ...formData, schedule_type: e.target.value as ScheduleType })}
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-cyan-500"
                  >
                    <option value="interval">Interval (Seconds)</option>
                    <option value="cron">Cron Expression</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Active Status</label>
                  <div className="pt-2">
                    <label className="inline-flex items-center cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.is_active}
                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                        className="sr-only peer"
                      />
                      <div className="w-11 h-6 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-slate-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-cyan-500 relative"></div>
                      <span className="ml-3 text-xs font-medium text-slate-300">
                        {formData.is_active ? 'Active' : 'Paused'}
                      </span>
                    </label>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Schedule Expression *</label>
                <input
                  type="text"
                  value={formData.schedule_expression}
                  onChange={(e) => setFormData({ ...formData, schedule_expression: e.target.value })}
                  placeholder={formData.schedule_type === 'interval' ? '60' : '*/5 * * * *'}
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm font-mono focus:outline-none focus:border-cyan-500"
                />
                <p className="text-[11px] text-slate-500 mt-1">
                  {formData.schedule_type === 'interval'
                    ? 'Enter number of seconds between runs (e.g. 60 for 1 minute, 300 for 5 minutes).'
                    : 'Enter standard 5-field cron syntax (e.g. "0 9 * * *" for 9am daily, "*/5 * * * *" for every 5 mins).'}
                </p>
              </div>

              <div className="flex justify-end space-x-3 border-t border-slate-800 pt-4">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-sm font-semibold transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting}
                  className="px-4 py-2 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white rounded-xl text-sm font-semibold shadow-lg shadow-cyan-500/20 transition-all disabled:opacity-50"
                >
                  {submitting ? 'Saving...' : editingSchedule ? 'Update Schedule' : 'Create Schedule'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
