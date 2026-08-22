import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api/client";

export default function SearchQueriesPage() {
  const queryClient = useQueryClient();
  const [text, setText] = useState("");

  const { data: queries } = useQuery<any[]>({
    queryKey: ["search-queries"],
    queryFn: async () => (await api.get("/search-queries")).data,
  });

  const createQuery = useMutation({
    mutationFn: () => api.post("/search-queries", { text }),
    onSuccess: () => {
      setText("");
      queryClient.invalidateQueries({ queryKey: ["search-queries"] });
    },
  });

  const deleteQuery = useMutation({
    mutationFn: (id: string) => api.delete(`/search-queries/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["search-queries"] }),
  });

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">שאילתות חיפוש</h1>
      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4 flex gap-2">
        <input
          placeholder='למשל: "מכרז ריהוט מוסדי"'
          value={text}
          onChange={(e) => setText(e.target.value)}
          className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <button onClick={() => text.trim() && createQuery.mutate()} className="bg-brand-600 text-white px-4 rounded-lg text-sm">
          הוסף
        </button>
      </div>
      <div className="space-y-2">
        {queries?.map((q) => (
          <div key={q.id} className="bg-white rounded-xl border border-slate-200 p-3 flex items-center justify-between">
            <div>
              <div className="font-medium text-navy-900">{q.text}</div>
              <div className="text-xs text-slate-500">
                {q.result_count} תוצאות · הרצה אחרונה: {q.last_run_at ? new Date(q.last_run_at).toLocaleString("he-IL") : "טרם הורצה"}
              </div>
            </div>
            <button onClick={() => deleteQuery.mutate(q.id)} className="text-red-500 text-xs">מחק</button>
          </div>
        ))}
        {!queries?.length && <div className="text-sm text-slate-400">אין עדיין שאילתות חיפוש מוגדרות.</div>}
      </div>
    </div>
  );
}
