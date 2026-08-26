export type ExecutionStatus = 'pending' | 'running' | 'passed' | 'failed' | 'timeout' | 'cancelled';
export type TriggerType = 'manual' | 'scheduled';

export interface ExecutionSummary {
  id: number;
  test_id: number;
  schedule_id?: number | null;
  status: ExecutionStatus;
  started_at?: string | null;
  finished_at?: string | null;
  duration?: number | null;
  exit_code?: number | null;
  trigger_type: TriggerType;
  created_at: string;
}

export interface ExecutionDetail extends ExecutionSummary {
  stdout?: string | null;
  stderr?: string | null;
  test_name?: string | null;
  test_framework?: string | null;
  schedule_expression?: string | null;
}

export interface ExecutionListResponse {
  items: ExecutionSummary[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ExecutionStats {
  total_executions: number;
  passed: number;
  failed: number;
  timeout: number;
  cancelled: number;
  pending: number;
  running: number;
  success_rate: number;
  average_duration: number;
}
