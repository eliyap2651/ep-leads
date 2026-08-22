import { Link } from "react-router-dom";
import { Lead, STATUS_LABELS, TIER_COLORS, TIER_LABELS } from "@/api/types";

export default function LeadCard({ lead }: { lead: Lead }) {
  return (
    <Link
      to={`/leads/${lead.id}`}
      className="block bg-white rounded-xl shadow-sm border border-slate-200 p-4 mb-3 active:scale-[0.99] transition"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-[11px] font-bold px-2 py-0.5 rounded ${TIER_COLORS[lead.tier]}`}>
              {TIER_LABELS[lead.tier]}
            </span>
            <span className="text-[11px] text-slate-400">{lead.score}/100</span>
          </div>
          <div className="font-semibold text-navy-900 truncate">{lead.title}</div>
          <div className="text-sm text-slate-500 mt-0.5">
            {lead.domain || "תחום לא ידוע"} · {lead.city || "עיר לא ידועה"}
          </div>
        </div>
        {lead.estimated_value ? (
          <div className="text-left shrink-0">
            <div className="text-sm font-bold text-navy-800">₪{Math.round(lead.estimated_value).toLocaleString()}</div>
          </div>
        ) : null}
      </div>

      <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500">
        <span className="px-2 py-1 rounded-full bg-slate-100">{STATUS_LABELS[lead.status]}</span>
        <div className="flex items-center gap-2">
          {lead.deadline && <span>⏰ {new Date(lead.deadline).toLocaleDateString("he-IL")}</span>}
          {lead.has_phone && <span className="text-green-600">📞</span>}
          {!lead.has_contact && <span className="text-red-500">ללא איש קשר</span>}
        </div>
      </div>
    </Link>
  );
}
