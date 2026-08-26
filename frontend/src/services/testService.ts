import { api } from './api';
import type { ExecutionListResponse } from '../types/execution';
import type { TestCreate, TestItem, TestListResponse, TestUpdate } from '../types/test';

export const testService = {
  async getTests(page = 1, page_size = 10): Promise<TestListResponse> {
    const response = await api.get<TestListResponse>('/tests', {
      params: { page, page_size },
    });
    return response.data;
  },

  async getTestById(id: number): Promise<TestItem> {
    const response = await api.get<TestItem>(`/tests/${id}`);
    return response.data;
  },

  async createTest(data: TestCreate): Promise<TestItem> {
    const response = await api.post<TestItem>('/tests', data);
    return response.data;
  },

  async updateTest(id: number, data: TestUpdate): Promise<TestItem> {
    const response = await api.put<TestItem>(`/tests/${id}`, data);
    return response.data;
  },

  async deleteTest(id: number): Promise<void> {
    await api.delete(`/tests/${id}`);
  },

  async getTestExecutions(testId: number, page = 1, page_size = 10, status?: string, trigger_type?: string): Promise<ExecutionListResponse> {
    const response = await api.get<ExecutionListResponse>(`/tests/${testId}/executions`, {
      params: { page, page_size, status, trigger_type },
    });
    return response.data;
  },
};
