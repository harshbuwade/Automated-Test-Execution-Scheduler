export type TestStatus = 'active' | 'inactive' | 'deprecated';

export interface TestItem {
  id: number;
  user_id: number;
  name: string;
  description?: string | null;
  script_path: string;
  framework: string;
  timeout: number;
  status: TestStatus;
  created_at: string;
  updated_at: string;
}

export interface TestCreate {
  name: string;
  description?: string;
  script_path: string;
  framework?: string;
  timeout?: number;
  status?: TestStatus;
}

export interface TestUpdate {
  name?: string;
  description?: string;
  script_path?: string;
  framework?: string;
  timeout?: number;
  status?: TestStatus;
}

export interface TestListResponse {
  items: TestItem[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
