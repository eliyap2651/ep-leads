import { useQuery } from "@tanstack/react-query";
import api from "@/api/client";

const STAGE_LABELS: Record<string, string> = {
  planning: "תכנון", approval: "אישור", construction: "בנייה", renovation: "שיפוץ", pre_procurement: "לפני רכש",
};

export default function ProjectsPage() {
  const { data: projects } = useQuery<any[]>({
    queryKey: ["projects"],
    queryFn: async () => (await api.get("/projects")).data,
  });

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">פרויקטים מוקדמים (לפני מכרז)</h1>
      <div className="space-y-2">
        {projects?.map((p) => (
          <div key={p.id} className="bg-white rounded-xl border border-slate-200 p-3">
            <div className="font-semibold text-navy-900">{p.name || "ללא שם"}</div>
            <div className="text-xs text-slate-500 mt-1">
              שלב: {p.stage ? STAGE_LABELS[p.stage] : "לא נמצא"} · {p.city || "לא נמצא"}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              יזם: {p.developer || "לא נמצא"} · קבלן: {p.contractor || "לא נמצא"} · אדריכל: {p.architect || "לא נמצא"}
            </div>
            {p.source_url && (
              <a href={p.source_url} target="_blank" rel="noreferrer" className="text-xs text-brand-600 underline">
                מקור
              </a>
            )}
          </div>
        ))}
        {!projects?.length && (
          <div className="text-sm text-slate-400 bg-white rounded-xl p-4 border border-slate-200">
            אין עדיין פרויקטים מוקדמים במערכת - אלה מתגלים אוטומטית ע״י מנוע ה-AI מתוך חדשות עסקיות וסריקות מקורות.
          </div>
        )}
      </div>
    </div>
  );
}
