import { useQuery } from "@tanstack/react-query";
import api from "@/api/client";

const WINDOWS = [
  { key: "today", label: "היום" },
  { key: "tomorrow", label: "מחר" },
  { key: "3_days", label: "3 ימים" },
  { key: "7_days", label: "7 ימים" },
  { key: "30_days", label: "30 יום" },
];

export default function TendersClosingPage() {
  const { data: counts } = useQuery<Record<string, number>>({
    queryKey: ["tenders-closing"],
    queryFn: async () => (await api.get("/analytics/tenders-closing")).data,
  });

  const { data: tenders } = useQuery<any[]>({
    queryKey: ["tenders", "open"],
    queryFn: async () => (await api.get("/tenders", { params: { is_open: true } })).data,
  });

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">מכרזים שעומדים להיסגר</h1>
      <div className="grid grid-cols-5 gap-2 mb-4">
        {WINDOWS.map((w) => (
          <div key={w.key} className="bg-white rounded-xl border border-slate-200 p-3 text-center">
            <div className="text-lg font-extrabold text-hot">{counts?.[w.key] ?? "—"}</div>
            <div className="text-[11px] text-slate-500">{w.label}</div>
          </div>
        ))}
      </div>

      <div className="space-y-2">
        {tenders?.map((t) => (
          <div key={t.id} className="bg-white rounded-xl border border-slate-200 p-3">
            <div className="font-semibold text-navy-900">{t.title || "ללא כותרת"}</div>
            <div className="text-xs text-slate-500 mt-1">
              {t.publishing_body || "לא נמצא"} · מס׳ {t.tender_number || "לא נמצא"}
            </div>
            <div className="text-xs mt-1">
              מועד אחרון: {t.submission_deadline ? new Date(t.submission_deadline).toLocaleDateString("he-IL") : "לא נמצא"}
            </div>
            {t.source_url && (
              <a href={t.source_url} target="_blank" rel="noreferrer" className="text-xs text-brand-600 underline">
                פתח מכרז במקור
              </a>
            )}
          </div>
        ))}
        {!tenders?.length && <div className="text-sm text-slate-400">אין מכרזים פתוחים כרגע במערכת.</div>}
      </div>
    </div>
  );
}
