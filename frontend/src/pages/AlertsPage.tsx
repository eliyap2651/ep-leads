import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api/client";

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const { data: alerts } = useQuery<any[]>({
    queryKey: ["alerts"],
    queryFn: async () => (await api.get("/alerts")).data,
  });

  const markRead = useMutation({
    mutationFn: (id: string) => api.post(`/alerts/${id}/read`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">התראות</h1>
      <div className="space-y-2">
        {alerts?.map((a) => (
          <div
            key={a.id}
            onClick={() => !a.is_read && markRead.mutate(a.id)}
            className={`rounded-xl border p-3 ${a.is_read ? "bg-white border-slate-200" : "bg-brand-50 border-brand-200"}`}
          >
            <div className="font-semibold text-navy-900 text-sm">{a.title}</div>
            {a.body && <div className="text-xs text-slate-600 mt-1">{a.body}</div>}
            <div className="text-[11px] text-slate-400 mt-1">{new Date(a.created_at).toLocaleString("he-IL")}</div>
          </div>
        ))}
        {!alerts?.length && <div className="text-sm text-slate-400">אין התראות חדשות.</div>}
      </div>
    </div>
  );
}
