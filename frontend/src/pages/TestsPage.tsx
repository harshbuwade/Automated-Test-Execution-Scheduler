import React, { useEffect, useState } from 'react';
import {
  AlertCircle,
  Edit2,
  Plus,
  Play,
  Search,
  Trash2,
  X,
} from 'lucide-react';
import { executionService } from '../services/executionService';
import { testService } from '../services/testService';
import type { ExecutionDetail } from '../types/execution';
import type { TestCreate, TestItem } from '../types/test';

export const TestsPage: React.FC = () => {
  const [tests, setTests] = useState<TestItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTest, setEditingTest] = useState<TestItem | null>(null);
  const [formData, setFormData] = useState<TestCreate>({
    name: '',
    description: '',
    script_path: 'sample_pass.py',
    framework: 'pytest',
    timeout: 30,
    status: 'active',
  });
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [runResult, setRunResult] = useState<ExecutionDetail | null>(null);
  const [runningTestId, setRunningTestId] = useState<number | null>(null);

  const fetchTests = async () => {
    try {
      setLoading(true);
      const res = await testService.getTests(page, 10);
      setTests(res.items);
      setTotalPages(res.total_pages);
    } catch (err) {
      console.error('Failed to fetch tests:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTests();
  }, [page]);

  const handleOpenCreateModal = () => {
    setEditingTest(null);
    setFormData({
      name: '',
      description: '',
      script_path: 'sample_pass.py',
      framework: 'pytest',
      timeout: 30,
      status: 'active',
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleOpenEditModal = (test: TestItem) => {
    setEditingTest(test);
    setFormData({
      name: test.name,
      description: test.description || '',
      script_path: test.script_path,
      framework: test.framework,
      timeout: test.timeout,
      status: test.status,
    });
    setFormError(null);
    setIsModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    if (!formData.name || !formData.script_path) {
      setFormError('Name and Script Path are required.');
      return;
    }

    try {
      setSubmitting(true);
      if (editingTest) {
        await testService.updateTest(editingTest.id, formData);
      } else {
        await testService.createTest(formData);
      }
      setIsModalOpen(false);
      fetchTests();
    } catch (err: any) {
      setFormError(err.response?.data?.detail || 'Failed to save test script definition.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (testId: number) => {
    if (!window.confirm('Are you sure you want to delete this test script definition?')) return;

    try {
      await testService.deleteTest(testId);
      fetchTests();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to delete test script.');
    }
  };

  const handleRunNow = async (testId: number) => {
    try {
      setRunningTestId(testId);
      const result = await executionService.triggerExecution(testId);
      setRunResult(result);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Execution trigger failed.');
    } finally {
      setRunningTestId(null);
    }
  };

  const filteredTests = tests.filter(
    (t) =>
      t.name.toLowerCase().includes(search.toLowerCase()) ||
      t.script_path.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search tests by name or script path..."
            className="w-full pl-10 pr-4 py-2 bg-slate-900 border border-slate-800 rounded-xl text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <button
          onClick={handleOpenCreateModal}
          className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold rounded-xl text-sm shadow-lg shadow-cyan-500/20 transition-all"
        >
          <Plus className="w-4 h-4" />
          <span>New Test Script</span>
        </button>
      </div>

      <div className="bg-slate-900/60 border border-slate-800/80 rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 text-xs font-semibold uppercase bg-slate-900/80">
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Script Path</th>
                <th className="py-3 px-4">Framework</th>
                <th className="py-3 px-4">Timeout</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Created</th>
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
              ) : filteredTests.length > 0 ? (
                filteredTests.map((test) => (
                  <tr key={test.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-3.5 px-4 font-semibold text-slate-100">
                      <div>{test.name}</div>
                      {test.description && <p className="text-xs text-slate-500 font-normal truncate max-w-xs">{test.description}</p>}
                    </td>
                    <td className="py-3.5 px-4 font-mono text-xs text-cyan-400">
                      <span className="bg-slate-950 px-2 py-1 rounded border border-slate-800">{test.script_path}</span>
                    </td>
                    <td className="py-3.5 px-4 text-slate-300 capitalize">{test.framework}</td>
                    <td className="py-3.5 px-4 text-slate-300">{test.timeout}s</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                        {test.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-400">
                      {new Date(test.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => handleRunNow(test.id)}
                          disabled={runningTestId === test.id}
                          className="flex items-center space-x-1 px-3 py-1.5 bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-lg text-xs font-semibold transition-all disabled:opacity-50"
                        >
                          {runningTestId === test.id ? (
                            <div className="w-3.5 h-3.5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin"></div>
                          ) : (
                            <Play className="w-3.5 h-3.5 fill-current" />
                          )}
                          <span>Run Now</span>
                        </button>

                        <button
                          onClick={() => handleOpenEditModal(test)}
                          className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-lg transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>

                        <button
                          onClick={() => handleDelete(test.id)}
                          className="p-1.5 hover:bg-rose-500/10 text-slate-400 hover:text-rose-400 rounded-lg transition-colors"
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
                    No test scripts found. Click "New Test Script" to create one.
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
                {editingTest ? 'Edit Test Script' : 'Create Test Script'}
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
              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Test Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. User Authentication Test Suite"
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Description</label>
                <textarea
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional description of what this test suite checks..."
                  rows={2}
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-400 mb-1">Script Path *</label>
                <input
                  type="text"
                  value={formData.script_path}
                  onChange={(e) => setFormData({ ...formData, script_path: e.target.value })}
                  placeholder="sample_pass.py"
                  required
                  className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm font-mono focus:outline-none focus:border-cyan-500"
                />
                <p className="text-[11px] text-slate-500 mt-1">Relative to test_scripts/ directory (e.g. sample_pass.py, sample_fail.py, sample_timeout.py).</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Framework</label>
                  <select
                    value={formData.framework}
                    onChange={(e) => setFormData({ ...formData, framework: e.target.value })}
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-cyan-500"
                  >
                    <option value="pytest">pytest</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1">Timeout (seconds)</label>
                  <input
                    type="number"
                    value={formData.timeout}
                    onChange={(e) => setFormData({ ...formData, timeout: parseInt(e.target.value) || 30 })}
                    min={1}
                    max={300}
                    className="w-full px-3.5 py-2.5 bg-slate-950 border border-slate-800 rounded-xl text-slate-100 text-sm focus:outline-none focus:border-cyan-500"
                  />
                </div>
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
                  {submitting ? 'Saving...' : editingTest ? 'Update Test' : 'Create Test'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {runResult && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="text-base font-bold text-slate-100 flex items-center space-x-2">
                <span>Execution Result for</span>
                <span className="text-cyan-400">#{runResult.id}</span>
              </h3>
              <button onClick={() => setRunResult(null)} className="text-slate-400 hover:text-slate-200">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-3 gap-3 text-xs bg-slate-950 p-3 rounded-xl border border-slate-800">
              <div>
                <span className="text-slate-500 block">Status</span>
                <span className="font-bold capitalize text-slate-200">{runResult.status}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Exit Code</span>
                <span className="font-mono font-bold text-slate-200">{runResult.exit_code}</span>
              </div>
              <div>
                <span className="text-slate-500 block">Duration</span>
                <span className="font-bold text-slate-200">{runResult.duration}s</span>
              </div>
            </div>

            <div className="space-y-2">
              <span className="text-xs font-semibold text-slate-400">Output Log</span>
              <pre className="p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-slate-300 max-h-48 overflow-y-auto whitespace-pre-wrap">
                {runResult.stdout || runResult.stderr || 'No output recorded.'}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setRunResult(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
