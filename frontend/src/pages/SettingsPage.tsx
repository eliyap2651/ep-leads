import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api/client";

const KNOWN_SETTINGS = [
  { key: "lead_score_threshold_hot", label: "סף ציון HOT", default: "90" },
  { key: "lead_score_threshold_high", label: "סף ציון HIGH", default: "75" },
  { key: "lead_score_threshold_medium", label: "סף ציון MEDIUM", default: "55" },
];

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const { data: settings } = useQuery<any[]>({
    queryKey: ["settings"],
    queryFn: async () => (await api.get("/settings")).data,
  });

  const upsert = useMutation({
    mutationFn: (payload: { key: string; value: string }) => api.put("/settings", payload),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["settings"] }),
  });

  const [local, setLocal] = useState<Record<string, string>>({});

  function valueFor(key: string, fallback: string) {
    const existing = settings?.find((s) => s.key === key)?.value;
    return local[key] ?? existing ?? fallback;
  }

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">הגדרות</h1>

      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-4">
        <div className="text-sm font-semibold mb-3">ספי ניקוד לידים</div>
        {KNOWN_SETTINGS.map((s) => (
          <div key={s.key} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
            <span className="text-sm text-slate-600">{s.label}</span>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={valueFor(s.key, s.default)}
                onChange={(e) => setLocal({ ...local, [s.key]: e.target.value })}
                onBlur={(e) => upsert.mutate({ key: s.key, value: e.target.value })}
                className="w-20 rounded-lg border border-slate-300 px-2 py-1 text-sm text-center"
              />
            </div>
          </div>
        ))}
      </div>

      <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
        מפתחות API (Anthropic, Serper/Bing, SMTP) מוגדרים אך ורק בקובץ <code>.env</code> בשרת ולא מוצגים כאן
        ולא ניתנים לעריכה דרך הממשק - מטעמי אבטחה (ראה מדריך ההתקנה).
      </div>
    </div>
  );
}
