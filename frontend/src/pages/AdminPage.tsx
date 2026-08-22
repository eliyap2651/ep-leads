import { useQuery } from "@tanstack/react-query";
import api from "@/api/client";
import StatCard from "@/components/StatCard";

export default function AdminPage() {
  const { data: health } = useQuery<any>({
    queryKey: ["admin-health"],
    queryFn: async () => (await api.get("/admin/health")).data,
    refetchInterval: 30_000,
  });

  const { data: runs } = useQuery<any[]>({
    queryKey: ["admin-scan-runs"],
    queryFn: async () => (await api.get("/admin/scan-runs")).data,
  });

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">ניטור מערכת</h1>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <StatCard label="בסיס נתונים" value={health?.database === "ok" ? "תקין ✓" : "שגיאה ✗"} accent={health?.database === "ok" ? "text-green-600" : "text-hot"} />
        <StatCard label="AI מוגדר" value={health?.ai_configured ? "כן" : "לא"} accent={health?.ai_configured ? "text-green-600" : "text-medium"} />
        <StatCard label="חיפוש מוגדר" value={health?.search_configured ? "כן" : "לא"} accent={health?.search_configured ? "text-green-600" : "text-medium"} />
        <StatCard label="Email מוגדר" value={health?.email_configured ? "כן" : "לא"} accent={health?.email_configured ? "text-green-600" : "text-medium"} />
        <StatCard label="מקורות פעילים" value={health?.sources_active ?? "—"} />
        <StatCard label="מקורות עם שגיאה" value={health?.sources_with_errors ?? "—"} accent="text-hot" />
        <StatCard label="עבודות שהצליחו" value={health?.successful_jobs ?? "—"} accent="text-green-600" />
        <StatCard label="עבודות שנכשלו" value={health?.failed_jobs ?? "—"} accent="text-hot" />
      </div>

      <div className="text-xs text-slate-400 mb-4">סריקה אחרונה: {health?.last_scan_at ? new Date(health.last_scan_at).toLocaleString("he-IL") : "טרם בוצעה"}</div>

      <div className="bg-white rounded-xl border border-slate-200 p-3">
        <div className="text-sm font-semibold mb-2">היסטוריית סריקות</div>
        <div className="space-y-2">
          {runs?.map((r) => (
            <div key={r.id} className="text-xs border-b border-slate-100 last:border-0 py-2 flex items-center justify-between">
              <div>
                <div className="font-medium">{r.task_name}</div>
                <div className="text-slate-400">{r.started_at ? new Date(r.started_at).toLocaleString("he-IL") : ""}</div>
              </div>
              <div className="text-left">
                <span className={`px-2 py-0.5 rounded-full ${r.status === "success" ? "bg-green-100 text-green-700" : r.status === "failed" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-500"}`}>
                  {r.status}
                </span>
                <div className="text-slate-400 mt-1">{r.items_found} תוצאות · {r.new_leads} חדשים</div>
              </div>
            </div>
          ))}
          {!runs?.length && <div className="text-sm text-slate-400">אין עדיין היסטוריית סריקות.</div>}
        </div>
      </div>
    </div>
  );
}
