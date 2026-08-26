export type ScheduleType = 'interval' | 'cron';

export interface ScheduleItem {
  id: number;
  test_id: number;
  schedule_type: ScheduleType;
  schedule_expression: string;
  is_active: boolean;

  next_run?: string | null;
  last_run?: string | null;
  created_at: string;
  test_name?: string;
}

export interface ScheduleCreate {
  test_id: number;
  schedule_type: ScheduleType;
  schedule_expression: string;
  is_active?: boolean;
}

export interface ScheduleUpdate {
  schedule_type?: ScheduleType;
  schedule_expression?: string;
  is_active?: boolean;
}

export interface ScheduleListResponse {
  items: ScheduleItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
