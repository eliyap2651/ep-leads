import { useQuery } from "@tanstack/react-query";
import api from "@/api/client";
import StatCard from "@/components/StatCard";
import LeadCard from "@/components/LeadCard";
import { DashboardStats, Lead } from "@/api/types";

export default function DashboardPage() {
  const { data: stats } = useQuery<DashboardStats>({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get("/analytics/dashboard")).data,
  });

  const { data: top } = useQuery<any[]>({
    queryKey: ["top-opportunities"],
    queryFn: async () => (await api.get("/analytics/top-opportunities", { params: { limit: 10 } })).data,
  });

  const { data: hotLeads } = useQuery<Lead[]>({
    queryKey: ["leads", "hot"],
    queryFn: async () => (await api.get("/leads", { params: { tier: "hot", limit: 5 } })).data,
  });

  return (
    <div>
      <h1 className="text-xl md:text-2xl font-extrabold text-navy-900 mb-4">הזדמנויות היום</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard label="סה״כ לידים" value={stats?.total_leads ?? "—"} />
        <StatCard label="לידים חדשים היום" value={stats?.new_today ?? "—"} />
        <StatCard label="לידים חמים" value={stats?.hot_leads ?? "—"} accent="text-hot" />
        <StatCard label="מכרזים פתוחים" value={stats?.open_tenders ?? "—"} />
        <StatCard label="נסגרים השבוע" value={stats?.closing_this_week ?? "—"} accent="text-high" />
        <StatCard label="פרויקטים חדשים היום" value={stats?.new_projects_today ?? "—"} />
        <StatCard label="לידים עם איש קשר" value={stats?.leads_with_contact ?? "—"} />
        <StatCard
          label="שווי פוטנציאלי משוער"
          value={stats ? `₪${Math.round(stats.estimated_pipeline_value).toLocaleString()}` : "—"}
          accent="text-brand-600"
        />
      </div>

      <h2 className="text-lg font-bold text-navy-900 mb-2">לידים חמים</h2>
      <div className="mb-6">
        {hotLeads?.length ? hotLeads.map((lead) => <LeadCard key={lead.id} lead={lead} />) : (
          <div className="text-sm text-slate-400 bg-white rounded-xl p-4 border border-slate-200">
            אין עדיין לידים חמים - הפעל סריקה מתוך מסך "מקורות מידע" כדי להתחיל לאסוף נתונים אמיתיים.
          </div>
        )}
      </div>

      <h2 className="text-lg font-bold text-navy-900 mb-2">Top 10 הזדמנויות</h2>
      <div className="space-y-2">
        {top?.map((item) => (
          <div key={item.id} className="bg-white rounded-xl border border-slate-200 p-3">
            <div className="font-semibold text-navy-900">{item.title}</div>
            <div className="text-xs text-slate-500 mt-1">ציון {item.score} · {item.tier.toUpperCase()}</div>
            {item.ai_summary && <div className="text-xs text-slate-600 mt-1">{item.ai_summary}</div>}
          </div>
        ))}
        {!top?.length && <div className="text-sm text-slate-400">אין עדיין נתונים.</div>}
      </div>
    </div>
  );
}
