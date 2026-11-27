const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8003/api/v1";

export type DemoLoginResult = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    role: string;
    organization_id: string;
    display_name: string;
  };
};

export type Page<T> = {
  items: T[];
  meta: { page: number; page_size: number; total: number };
};

export type Customer = {
  id: string;
  organization_id: string;
  name: string;
  email: string | null;
  phone: string | null;
  notes: string | null;
};

export type ServiceLocation = {
  id: string;
  organization_id: string;
  customer_id: string;
  name: string;
  address_line1: string;
  city: string;
  region: string | null;
  postal_code: string | null;
  country: string;
};

export type WorkOrder = {
  id: string;
  organization_id: string;
  customer_id: string;
  service_location_id: string | null;
  title: string;
  description: string | null;
  status: string;
  priority: string;
  due_at: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  technician_id: string | null;
  technician_name: string | null;
  overlap_warning: boolean;
  overlapping_work_order_ids: string[];
  updated_at: string;
};

export type Technician = {
  id: string;
  display_name: string;
  email: string;
  skills: string | null;
};

export type ScheduleItem = {
  work_order_id: string;
  title: string;
  status: string;
  priority: string;
  customer_id: string;
  technician_id: string | null;
  technician_name: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  due_at: string | null;
  overlap_warning: boolean;
  overlapping_work_order_ids: string[];
};

export type Assignment = {
  id: string;
  work_order_id: string;
  technician_id: string;
  technician_name: string | null;
  work_order_title: string | null;
  work_order_status: string | null;
  scheduled_start: string | null;
  scheduled_end: string | null;
  overlap_warning: boolean;
};

export type JobActivity = {
  id: string;
  work_order_id: string;
  activity_type: string;
  note: string | null;
  occurred_at: string;
};

export type Checklist = {
  id: string;
  work_order_id: string;
  name: string;
  items: {
    id: string;
    label: string;
    is_completed: boolean;
    is_required: boolean;
    updated_at: string;
  }[];
};

export type TimeEntry = {
  id: string;
  work_order_id: string;
  technician_id: string;
  started_at: string;
  ended_at: string | null;
  minutes: number | null;
  notes: string | null;
};

export type Asset = {
  id: string;
  organization_id: string;
  customer_id: string;
  service_location_id: string | null;
  name: string;
  serial_number: string | null;
  asset_type: string | null;
  manufacturer: string | null;
  model_number: string | null;
  warranty_expires_on: string | null;
  maintenance_notes: string | null;
  created_at?: string;
  updated_at?: string;
};

export type ServiceHistoryItem = {
  work_order_id: string;
  title: string;
  status: string;
  priority: string;
  customer_id: string;
  customer_name: string | null;
  asset_id: string | null;
  asset_name: string | null;
  scheduled_start: string | null;
  completed_note: string | null;
  updated_at: string;
};

export type Signoff = {
  id: string;
  organization_id: string;
  work_order_id: string;
  signer_name: string;
  signed_at: string;
  acknowledgement_text: string;
  signature_storage_key: string | null;
  is_certified_esignature: boolean;
  disclaimer: string;
};

export type PartUsed = {
  id: string;
  work_order_id: string;
  part_name: string;
  quantity: string;
  unit_cost: string | null;
  notes: string | null;
  line_total: string | null;
};

export type ServiceSummaryReport = {
  jobs_by_status: { status: string; count: number }[];
  total_jobs: number;
  completed_jobs: number;
  completion_rate: number;
  labor: {
    technician_id: string | null;
    technician_name: string | null;
    total_minutes: number;
    entry_count: number;
  }[];
  total_labor_minutes: number;
  parts: {
    part_name: string;
    total_quantity: string;
    total_cost: string | null;
  }[];
  parts_total_cost: string | null;
  generated_at: string;
};

export type PrintableServiceReport = {
  work_order: WorkOrder;
  customer_name: string | null;
  location_label: string | null;
  asset_name: string | null;
  notes: JobActivity[];
  checklists: {
    name: string;
    items: { label: string; is_completed: boolean; is_required: boolean }[];
  }[];
  time_entries: {
    technician_name: string | null;
    started_at: string;
    ended_at: string | null;
    minutes: number | null;
    notes: string | null;
  }[];
  parts: PartUsed[];
  signoffs: Signoff[];
  labor_minutes_total: number;
  parts_cost_total: string | null;
  print_hint: string;
};

export type AISource = {
  type: string;
  id: string;
  label: string;
};

export type ServiceReportDraft = {
  work_order_id: string;
  draft: {
    problem: string;
    diagnosis: string;
    work_performed: string;
    parts: string[];
    follow_up: string;
  };
  explanation: string;
  sources: AISource[];
  requires_confirmation: boolean;
  provider: string;
  ai_cannot: string[];
};

export type JobPrepResult = {
  work_order_id: string;
  summary: string;
  history_highlights: string[];
  existing_checklist: string[];
  suggested_checklist: { label: string; reason: string; confirmed: boolean }[];
  explanation: string;
  sources: AISource[];
  requires_confirmation: boolean;
  provider: string;
};

export type ServiceMemoryResult = {
  query: string;
  recurring_themes: string[];
  suggested_follow_up: string;
  hits: {
    work_order_id: string;
    title: string;
    status: string;
    customer_id: string;
    customer_name: string | null;
    asset_id: string | null;
    asset_name: string | null;
    note_excerpt: string | null;
    occurred_at: string | null;
  }[];
  explanation: string;
  sources: AISource[];
  requires_confirmation: boolean;
  provider: string;
};

function authHeaders(token: string): HeadersInit {
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    return (
      data?.detail?.error?.message ??
      data?.error?.message ??
      `Request failed (${res.status})`
    );
  } catch {
    return `Request failed (${res.status})`;
  }
}

export async function demoLogin(
  email: string,
  password: string
): Promise<DemoLoginResult> {
  const res = await fetch(`${API_BASE}/auth/demo-login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function apiGet<T>(path: string, token: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: authHeaders(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res.json();
}

export async function apiSend<T>(
  path: string,
  token: string,
  method: string,
  body?: unknown
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: authHeaders(token),
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await parseError(res));
  if (res.status === 204) return undefined as T;
  return res.json();
}
