export type LeadTier = "hot" | "high" | "medium" | "low";
export type RecordType = "tender" | "project";
export type LeadStatus =
  | "new" | "reviewed" | "contacted" | "info_sent" | "quote_sent"
  | "negotiation" | "won" | "lost" | "not_relevant" | "no_response";

export interface Lead {
  id: string;
  title: string;
  record_type: RecordType;
  domain: string | null;
  city: string | null;
  region: string;
  estimated_value: number | null;
  deadline: string | null;
  score: number;
  tier: LeadTier;
  status: LeadStatus;
  created_at: string;
  has_contact: boolean;
  has_phone: boolean;
}

export interface LeadDetail extends Lead {
  address: string | null;
  ai_summary: string | null;
  score_breakdown_json: string | null;
  company_id: string | null;
  assigned_to_id: string | null;
  is_stale: boolean;
  last_verified_at: string | null;
}

export interface DashboardStats {
  total_leads: number;
  new_today: number;
  hot_leads: number;
  open_tenders: number;
  closing_this_week: number;
  new_projects_today: number;
  leads_with_contact: number;
  leads_without_contact: number;
  estimated_pipeline_value: number;
}

export const STATUS_LABELS: Record<LeadStatus, string> = {
  new: "חדש",
  reviewed: "נבדק",
  contacted: "נוצר קשר",
  info_sent: "נשלח מידע",
  quote_sent: "הצעת מחיר",
  negotiation: "משא ומתן",
  won: "נסגר - זכינו",
  lost: "הפסדנו",
  not_relevant: "לא רלוונטי",
  no_response: "אין מענה",
};

export const TIER_LABELS: Record<LeadTier, string> = { hot: "HOT", high: "HIGH", medium: "MEDIUM", low: "LOW" };

export const TIER_COLORS: Record<LeadTier, string> = {
  hot: "bg-hot text-white",
  high: "bg-high text-white",
  medium: "bg-medium text-white",
  low: "bg-low text-white",
};
