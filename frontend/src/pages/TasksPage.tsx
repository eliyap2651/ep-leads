import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api/client";

export default function TasksPage() {
  const queryClient = useQueryClient();
  const [title, setTitle] = useState("");
  const [dueDate, setDueDate] = useState("");

  const { data: tasks } = useQuery<any[]>({
    queryKey: ["tasks"],
    queryFn: async () => (await api.get("/tasks")).data,
  });

  const createTask = useMutation({
    mutationFn: () => api.post("/tasks", { title, due_date: dueDate || null }),
    onSuccess: () => {
      setTitle("");
      setDueDate("");
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
  });

  const completeTask = useMutation({
    mutationFn: (id: string) => api.post(`/tasks/${id}/complete`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tasks"] }),
  });

  const today = new Date().toISOString().slice(0, 10);
  const overdue = tasks?.filter((t) => t.due_date && t.due_date < today) || [];
  const dueToday = tasks?.filter((t) => t.due_date === today) || [];
  const upcoming = tasks?.filter((t) => !t.due_date || t.due_date > today) || [];

  function Section({ label, items }: { label: string; items: any[] }) {
    if (!items.length) return null;
    return (
      <div className="mb-4">
        <div className="text-sm font-semibold text-slate-500 mb-2">{label}</div>
        <div className="space-y-2">
          {items.map((t) => (
            <div key={t.id} className="bg-white rounded-xl border border-slate-200 p-3 flex items-center justify-between">
              <div>
                <div className="font-medium text-navy-900">{t.title}</div>
                {t.due_date && <div className="text-xs text-slate-500">{new Date(t.due_date).toLocaleDateString("he-IL")}</div>}
              </div>
              <button onClick={() => completeTask.mutate(t.id)} className="text-green-600 text-sm">✓ סיום</button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">המשימות שלי</h1>
      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4 space-y-2">
        <input placeholder="משימה חדשה..." value={title} onChange={(e) => setTitle(e.target.value)} className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm" />
        <div className="flex gap-2">
          <input type="date" value={dueDate} onChange={(e) => setDueDate(e.target.value)} className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <button onClick={() => title.trim() && createTask.mutate()} className="bg-brand-600 text-white px-4 rounded-lg text-sm">הוסף</button>
        </div>
      </div>

      <Section label="באיחור" items={overdue} />
      <Section label="היום" items={dueToday} />
      <Section label="קרובות" items={upcoming} />
      {!tasks?.length && <div className="text-sm text-slate-400">אין משימות פתוחות.</div>}
    </div>
  );
}
