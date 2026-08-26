import { api } from './api';
import type { ExecutionListResponse } from '../types/execution';
import type { ScheduleCreate, ScheduleItem, ScheduleListResponse, ScheduleUpdate } from '../types/schedule';

export const scheduleService = {
  async getSchedules(page = 1, page_size = 10, test_id?: number, is_active?: boolean, schedule_type?: string): Promise<ScheduleListResponse> {
    const response = await api.get<ScheduleListResponse>('/schedules', {
      params: { page, page_size, test_id, is_active, schedule_type },
    });
    return response.data;
  },

  async getScheduleById(id: number): Promise<ScheduleItem> {
    const response = await api.get<ScheduleItem>(`/schedules/${id}`);
    return response.data;
  },

  async createSchedule(data: ScheduleCreate): Promise<ScheduleItem> {
    const response = await api.post<ScheduleItem>('/schedules', data);
    return response.data;
  },

  async updateSchedule(id: number, data: ScheduleUpdate): Promise<ScheduleItem> {
    const response = await api.put<ScheduleItem>(`/schedules/${id}`, data);
    return response.data;
  },

  async deleteSchedule(id: number): Promise<void> {
    await api.delete(`/schedules/${id}`);
  },

  async pauseSchedule(id: number): Promise<ScheduleItem> {
    const response = await api.post<ScheduleItem>(`/schedules/${id}/pause`);
    return response.data;
  },

  async resumeSchedule(id: number): Promise<ScheduleItem> {
    const response = await api.post<ScheduleItem>(`/schedules/${id}/resume`);
    return response.data;
  },

  async getScheduleExecutions(scheduleId: number, page = 1, page_size = 10): Promise<ExecutionListResponse> {
    const response = await api.get<ExecutionListResponse>(`/schedules/${scheduleId}/executions`, {
      params: { page, page_size },
    });
    return response.data;
  },
};
