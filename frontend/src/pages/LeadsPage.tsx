import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import api from "@/api/client";
import LeadCard from "@/components/LeadCard";
import { Lead } from "@/api/types";

export default function LeadsPage() {
  const [q, setQ] = useState("");
  const [tier, setTier] = useState("");
  const [domain, setDomain] = useState("");
  const [hasContact, setHasContact] = useState("");

  const { data: leads, isLoading } = useQuery<Lead[]>({
    queryKey: ["leads", q, tier, domain, hasContact],
    queryFn: async () =>
      (
        await api.get("/leads", {
          params: {
            q: q || undefined,
            tier: tier || undefined,
            domain: domain || undefined,
            has_contact: hasContact === "" ? undefined : hasContact === "true",
            limit: 100,
          },
        })
      ).data,
  });

  return (
    <div>
      <h1 className="text-xl font-extrabold text-navy-900 mb-3">לידים</h1>

      <div className="bg-white rounded-xl border border-slate-200 p-3 mb-3 space-y-2">
        <input
          placeholder="חיפוש חופשי (כותרת / עיר)..."
          value={q}
          onChange={(e) => setQ(e.target.value)}
          className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
        />
        <div className="grid grid-cols-3 gap-2">
          <select value={tier} onChange={(e) => setTier(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-2 text-sm">
            <option value="">כל הדירוגים</option>
            <option value="hot">HOT</option>
            <option value="high">HIGH</option>
            <option value="medium">MEDIUM</option>
            <option value="low">LOW</option>
          </select>
          <select value={domain} onChange={(e) => setDomain(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-2 text-sm">
            <option value="">כל התחומים</option>
            <option value="hotel">מלונאות</option>
            <option value="school">בתי ספר</option>
            <option value="kindergarten">גני ילדים</option>
            <option value="yeshiva">ישיבות</option>
            <option value="dormitory">פנימיות</option>
            <option value="nursing_home">בתי אבות</option>
            <option value="assisted_living">דיור מוגן</option>
            <option value="hospital">בתי חולים</option>
            <option value="university">אוניברסיטאות</option>
            <option value="municipality">רשויות</option>
            <option value="gov_company">חברות ממשלתיות</option>
            <option value="factory">מפעלים</option>
            <option value="office">משרדים</option>
          </select>
          <select value={hasContact} onChange={(e) => setHasContact(e.target.value)} className="rounded-lg border border-slate-300 px-2 py-2 text-sm">
            <option value="">הכל</option>
            <option value="true">עם איש קשר</option>
            <option value="false">ללא איש קשר</option>
          </select>
        </div>
      </div>

      {isLoading && <div className="text-sm text-slate-400">טוען...</div>}
      {!isLoading && !leads?.length && (
        <div className="text-sm text-slate-400 bg-white rounded-xl p-4 border border-slate-200">
          לא נמצאו לידים תואמים.
        </div>
      )}
      {leads?.map((lead) => (
        <LeadCard key={lead.id} lead={lead} />
      ))}
    </div>
  );
}
