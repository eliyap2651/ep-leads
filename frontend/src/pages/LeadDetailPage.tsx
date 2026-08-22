import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "@/api/client";
import { LeadDetail, STATUS_LABELS, TIER_COLORS, TIER_LABELS } from "@/api/types";

const STATUS_FLOW: (keyof typeof STATUS_LABELS)[] = [
  "new", "reviewed", "contacted", "info_sent", "quote_sent", "negotiation", "won",
];

export default function LeadDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [aiAdvice, setAiAdvice] = useState<any>(null);
  const [aiLoading, setAiLoading] = useState(false);
  const [aiError, setAiError] = useState<string | null>(null);

  const { data: lead } = useQuery<LeadDetail>({
    queryKey: ["lead", id],
    queryFn: async () => (await api.get(`/leads/${id}`)).data,
  });

  const { data: contacts } = useQuery<any[]>({
    queryKey: ["lead-contacts", id],
    queryFn: async () => (await api.get(`/contacts/lead/${id}`)).data,
  });

  const { data: notes } = useQuery<any[]>({
    queryKey: ["lead-notes", id],
    queryFn: async () => (await api.get(`/leads/${id}/notes`)).data,
  });

  const { data: activities } = useQuery<any[]>({
    queryKey: ["lead-activities", id],
    queryFn: async () => (await api.get(`/leads/${id}/activities`)).data,
  });

  const updateStatus = useMutation({
    mutationFn: (status: string) => api.patch(`/leads/${id}`, { status }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lead", id] });
      queryClient.invalidateQueries({ queryKey: ["lead-activities", id] });
    },
  });

  const addNote = useMutation({
    mutationFn: () => api.post(`/leads/${id}/notes`, { body: note }),
    onSuccess: () => {
      setNote("");
      queryClient.invalidateQueries({ queryKey: ["lead-notes", id] });
    },
  });

  const logActivity = useMutation({
    mutationFn: (activity_type: string) => api.post(`/leads/${id}/activities`, { activity_type }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["lead-activities", id] }),
  });

  async function askAI() {
    setAiLoading(true);
    setAiError(null);
    try {
      const { data } = await api.post(`/leads/${id}/ai-assistant`);
      setAiAdvice(data);
    } catch (err: any) {
      setAiError(err?.response?.data?.detail || "מנוע ה-AI אינו זמין כרגע");
    } finally {
      setAiLoading(false);
    }
  }

  if (!lead) return <div className="text-sm text-slate-400">טוען...</div>;

  const primaryPhone = contacts?.find((c) => c.phone)?.phone;
  const primaryWhatsapp = contacts?.find((c) => c.whatsapp)?.whatsapp;
  const primaryEmail = contacts?.find((c) => c.email)?.email;

  return (
    <div className="pb-6">
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-xs font-bold px-2 py-1 rounded ${TIER_COLORS[lead.tier]}`}>{TIER_LABELS[lead.tier]}</span>
        <span className="text-xs text-slate-400">ציון {lead.score}/100</span>
      </div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-1">{lead.title}</h1>
      <div className="text-sm text-slate-500 mb-4">
        {lead.domain || "לא נמצא"} · {lead.city || "לא נמצא"} · {lead.region}
      </div>

      {/* Quick actions - big touch targets, mobile-first (spec section 11) */}
      <div className="grid grid-cols-4 gap-2 mb-4">
        <a
          href={primaryPhone ? `tel:${primaryPhone}` : undefined}
          onClick={() => primaryPhone && logActivity.mutate("call")}
          className={`flex flex-col items-center justify-center gap-1 rounded-xl py-3 text-xs font-medium ${primaryPhone ? "bg-green-600 text-white" : "bg-slate-100 text-slate-400"}`}
        >
          📞 התקשר
        </a>
        <a
          href={primaryWhatsapp ? `https://wa.me/${primaryWhatsapp.replace(/\D/g, "")}` : undefined}
          target="_blank" rel="noreferrer"
          onClick={() => primaryWhatsapp && logActivity.mutate("whatsapp")}
          className={`flex flex-col items-center justify-center gap-1 rounded-xl py-3 text-xs font-medium ${primaryWhatsapp ? "bg-emerald-500 text-white" : "bg-slate-100 text-slate-400"}`}
        >
          💬 WhatsApp
        </a>
        <a
          href={primaryEmail ? `mailto:${primaryEmail}` : undefined}
          onClick={() => primaryEmail && logActivity.mutate("email")}
          className={`flex flex-col items-center justify-center gap-1 rounded-xl py-3 text-xs font-medium ${primaryEmail ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-400"}`}
        >
          ✉️ Email
        </a>
        <button
          onClick={askAI}
          className="flex flex-col items-center justify-center gap-1 rounded-xl py-3 text-xs font-medium bg-navy-900 text-white"
        >
          🤖 מה לעשות?
        </button>
      </div>

      {aiLoading && <div className="text-sm text-slate-400 mb-3">מנתח את הליד...</div>}
      {aiError && <div className="text-sm text-red-600 bg-red-50 rounded-lg p-3 mb-3">{aiError}</div>}
      {aiAdvice && (
        <div className="bg-navy-900 text-white rounded-xl p-4 mb-4 space-y-2 text-sm">
          <div><b>למה מעניין:</b> {aiAdvice.why_interesting}</div>
          <div><b>למי לפנות:</b> {aiAdvice.who_to_contact}</div>
          <div><b>מה לשאול:</b> {aiAdvice.what_to_ask}</div>
          <div><b>מה להציע:</b> {aiAdvice.what_to_offer}</div>
          <div><b>איך לפתוח:</b> {aiAdvice.how_to_open}</div>
          <div><b>הודעת WhatsApp מוכנה:</b> {aiAdvice.whatsapp_message}</div>
          <div><b>Next Step:</b> {aiAdvice.next_step} ({aiAdvice.follow_up_timing})</div>
        </div>
      )}

      {/* CRM status pipeline */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4">
        <div className="text-sm font-semibold mb-2">סטטוס</div>
        <div className="flex flex-wrap gap-2">
          {STATUS_FLOW.map((s) => (
            <button
              key={s}
              onClick={() => updateStatus.mutate(s)}
              className={`text-xs px-3 py-2 rounded-full font-medium ${
                lead.status === s ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
              }`}
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
          <button onClick={() => updateStatus.mutate("not_relevant")} className="text-xs px-3 py-2 rounded-full bg-red-50 text-red-600">
            לא רלוונטי
          </button>
          <button onClick={() => updateStatus.mutate("lost")} className="text-xs px-3 py-2 rounded-full bg-red-50 text-red-600">
            הפסדנו
          </button>
        </div>
      </div>

      {/* Contacts */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4">
        <div className="text-sm font-semibold mb-2">אנשי קשר</div>
        {contacts?.length ? (
          contacts.map((c) => (
            <div key={c.id} className="text-sm py-1 border-b border-slate-100 last:border-0">
              <div className="font-medium">{c.name || "לא נמצא"} {c.role ? `· ${c.role}` : ""}</div>
              <div className="text-slate-500 text-xs">
                {c.phone || "לא נמצא טלפון"} · {c.email || "לא נמצא מייל"} · אמינות: {c.confidence}
              </div>
            </div>
          ))
        ) : (
          <div className="text-sm text-slate-400">לא נמצא איש קשר</div>
        )}
      </div>

      {/* Notes */}
      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-4">
        <div className="text-sm font-semibold mb-2">הערות</div>
        <div className="flex gap-2 mb-3">
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="הוסף הערה..."
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm"
          />
          <button
            onClick={() => note.trim() && addNote.mutate()}
            className="bg-brand-600 text-white px-3 rounded-lg text-sm"
          >
            שמור
          </button>
        </div>
        {notes?.map((n) => (
          <div key={n.id} className="text-sm py-1 border-b border-slate-100 last:border-0">
            {n.body}
            <div className="text-xs text-slate-400">{new Date(n.created_at).toLocaleString("he-IL")}</div>
          </div>
        ))}
      </div>

      {/* Activity history */}
      <div className="bg-white rounded-xl border border-slate-200 p-3">
        <div className="text-sm font-semibold mb-2">היסטוריית פעולות</div>
        {activities?.map((a) => (
          <div key={a.id} className="text-xs text-slate-500 py-1 border-b border-slate-100 last:border-0">
            {a.activity_type}: {a.description} · {new Date(a.created_at).toLocaleString("he-IL")}
          </div>
        ))}
        {!activities?.length && <div className="text-sm text-slate-400">אין עדיין פעולות</div>}
      </div>
    </div>
  );
}
