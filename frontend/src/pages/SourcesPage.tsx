import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api/client";

export default function SourcesPage() {
  const queryClient = useQueryClient();
  const [form, setForm] = useState({ name: "", url: "", source_type: "html", scan_frequency: "daily" });

  const { data: sources } = useQuery<any[]>({
    queryKey: ["sources"],
    queryFn: async () => (await api.get("/sources")).data,
  });

  const createSource = useMutation({
    mutationFn: () => api.post("/sources", form),
    onSuccess: () => {
      setForm({ name: "", url: "", source_type: "html", scan_frequency: "daily" });
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
  });

  const runSearch = useMutation({
    mutationFn: () => api.post("/search/run"),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["sources"] }),
  });

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h1 className="text-xl font-extrabold text-navy-900">מקורות מידע</h1>
        <button
          onClick={() => runSearch.mutate()}
          disabled={runSearch.isPending}
          className="bg-navy-900 text-white text-sm px-4 py-2 rounded-lg"
        >
          {runSearch.isPending ? "סורק..." : "הרץ סריקה עכשיו"}
        </button>
      </div>

      {runSearch.data && (
        <div className="text-xs bg-brand-50 text-brand-700 rounded-lg p-3 mb-3">
          נמצאו {runSearch.data.data.new_leads} לידים חדשים, עודכנו {runSearch.data.data.updated_leads}.
          {runSearch.data.data.errors?.length ? ` שגיאות: ${runSearch.data.data.errors.join("; ")}` : ""}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4 space-y-2">
        <div className="text-sm font-semibold">הוספת מקור חדש</div>
        <input placeholder="שם המקור" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <input placeholder="URL" value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <div className="grid grid-cols-2 gap-2">
          <select value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value })} className="rounded-lg border border-slate-300 px-2 py-2 text-sm">
            <option value="html">דף HTML (רשימת מכרזים)</option>
            <option value="rss">RSS</option>
            <option value="sitemap">Sitemap</option>
          </select>
          <select value={form.scan_frequency} onChange={(e) => setForm({ ...form, scan_frequency: e.target.value })} className="rounded-lg border border-slate-300 px-2 py-2 text-sm">
            <option value="hourly">כל שעה</option>
            <option value="every_3h">כל 3 שעות</option>
            <option value="every_6h">כל 6 שעות</option>
            <option value="every_12h">כל 12 שעות</option>
            <option value="daily">פעם ביום</option>
            <option value="weekly">פעם בשבוע</option>
            <option value="none">ללא סריקה אוטומטית</option>
          </select>
        </div>
        <button
          onClick={() => form.name && form.url && createSource.mutate()}
          className="w-full bg-brand-600 text-white rounded-lg py-2 text-sm font-medium"
        >
          הוסף מקור
        </button>
      </div>

      <div className="space-y-2">
        {sources?.map((s) => (
          <div key={s.id} className="bg-white rounded-xl border border-slate-200 p-3">
            <div className="flex items-center justify-between">
              <div className="font-semibold text-navy-900">{s.name}</div>
              <span className={`text-[11px] px-2 py-0.5 rounded-full ${s.status === "ok" ? "bg-green-100 text-green-700" : s.status === "error" ? "bg-red-100 text-red-700" : "bg-slate-100 text-slate-500"}`}>
                {s.status}
              </span>
            </div>
            <div className="text-xs text-slate-500 mt-1 truncate">{s.url}</div>
            <div className="text-xs text-slate-500 mt-1">
              תוצאות אחרונות: {s.result_count} · סריקה אחרונה: {s.last_scan_at ? new Date(s.last_scan_at).toLocaleString("he-IL") : "טרם נסרק"}
            </div>
            {s.last_error && <div className="text-xs text-red-600 mt-1">שגיאה: {s.last_error}</div>}
          </div>
        ))}
        {!sources?.length && <div className="text-sm text-slate-400">עדיין לא הוגדרו מקורות מידע.</div>}
      </div>
    </div>
  );
}
