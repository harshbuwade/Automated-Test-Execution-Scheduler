import { api } from './api';
import type { ExecutionDetail, ExecutionListResponse, ExecutionStats, ExecutionSummary } from '../types/execution';

export const executionService = {
  async getExecutions(
    page = 1,
    page_size = 10,
    test_id?: number,
    schedule_id?: number,
    status?: string,
    trigger_type?: string,
    date_from?: string,
    date_to?: string
  ): Promise<ExecutionListResponse> {
    const response = await api.get<ExecutionListResponse>('/executions', {
      params: { page, page_size, test_id, schedule_id, status, trigger_type, date_from, date_to },
    });
    return response.data;
  },

  async getExecutionById(id: number): Promise<ExecutionDetail> {
    const response = await api.get<ExecutionDetail>(`/executions/${id}`);
    return response.data;
  },

  async getRecentExecutions(limit = 10): Promise<ExecutionSummary[]> {
    const response = await api.get<ExecutionSummary[]>('/executions/recent', {
      params: { limit },
    });
    return response.data;
  },

  async getExecutionStats(date_from?: string, date_to?: string): Promise<ExecutionStats> {
    const response = await api.get<ExecutionStats>('/executions/stats', {
      params: { date_from, date_to },
    });
    return response.data;
  },

  async triggerExecution(test_id: number): Promise<ExecutionDetail> {
    const response = await api.post<ExecutionDetail>('/executions', { test_id });
    return response.data;
  },
};
