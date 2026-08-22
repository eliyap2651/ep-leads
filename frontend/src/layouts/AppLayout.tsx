import { NavLink } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";

const NAV_ITEMS = [
  { to: "/", label: "בית", icon: "🏠" },
  { to: "/leads", label: "לידים", icon: "🎯" },
  { to: "/tenders-closing", label: "מכרזים", icon: "📄" },
  { to: "/tasks", label: "משימות", icon: "✅" },
  { to: "/alerts", label: "התראות", icon: "🔔" },
];

const DESKTOP_EXTRA_ITEMS = [
  { to: "/projects", label: "פרויקטים מוקדמים", icon: "🏗️" },
  { to: "/sources", label: "מקורות מידע", icon: "🌐" },
  { to: "/search-queries", label: "שאילתות חיפוש", icon: "🔍" },
  { to: "/settings", label: "הגדרות", icon: "⚙️" },
  { to: "/admin", label: "ניטור מערכת", icon: "🩺" },
];

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen bg-slate-50 text-navy-900" dir="rtl">
      {/* Desktop sidebar */}
      <div className="hidden md:flex">
        <aside className="fixed inset-y-0 right-0 w-64 bg-navy-900 text-white flex flex-col">
          <div className="p-5 border-b border-white/10">
            <div className="text-xl font-extrabold">EP LEADS</div>
            <div className="text-xs text-white/60 mt-1">מצא לי את העסקה הבאה שלי</div>
          </div>
          <nav className="flex-1 overflow-y-auto py-3">
            {[...NAV_ITEMS, ...DESKTOP_EXTRA_ITEMS].map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-5 py-3 text-sm font-medium transition ${
                    isActive ? "bg-brand-600 text-white" : "text-white/80 hover:bg-white/10"
                  }`
                }
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </NavLink>
            ))}
          </nav>
          <div className="p-4 border-t border-white/10 text-sm">
            <div className="font-semibold">{user?.full_name}</div>
            <div className="text-white/50 text-xs mb-2">{user?.role}</div>
            <button onClick={logout} className="text-white/70 hover:text-white text-xs underline">
              התנתקות
            </button>
          </div>
        </aside>
        <main className="mr-64 flex-1 p-6 w-full">{children}</main>
      </div>

      {/* Mobile layout */}
      <div className="md:hidden">
        <header className="sticky top-0 z-20 bg-navy-900 text-white px-4 py-3 flex items-center justify-between">
          <div className="font-extrabold text-lg">EP LEADS</div>
          <button onClick={logout} className="text-xs text-white/70">
            יציאה
          </button>
        </header>
        <main className="p-3 pb-24">{children}</main>
        <nav className="fixed bottom-0 inset-x-0 z-30 bg-white border-t border-slate-200 safe-bottom">
          <div className="grid grid-cols-5">
            {NAV_ITEMS.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === "/"}
                className={({ isActive }) =>
                  `flex flex-col items-center justify-center py-2 text-[11px] font-medium ${
                    isActive ? "text-brand-600" : "text-slate-500"
                  }`
                }
              >
                <span className="text-lg">{item.icon}</span>
                {item.label}
              </NavLink>
            ))}
          </div>
        </nav>
      </div>
    </div>
  );
}
