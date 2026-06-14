import { Bell, Menu, Search } from "lucide-react";
import { useLocation } from "react-router-dom";
import { useAuthenticatedUser } from "../../context/AuthContext";

const routeTitles: Record<string, string> = {
  "/chat": "Company Knowledge",
  "/sources": "Knowledge Sources",
  "/documents": "Document Library",
  "/reports": "Usage Reports",
  "/admin/ingestion": "Ingestion Queue",
  "/admin/users": "Users & Roles",
  "/admin/audit-logs": "Audit Logs",
  "/admin/evaluation": "Evaluation",
  "/admin/settings": "Settings",
};

export function TopBar({ onMenu }: { onMenu: () => void }) {
  const { pathname } = useLocation();
  const currentUser = useAuthenticatedUser();
  return (
    <header className="flex h-16 shrink-0 items-center justify-between border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-950 sm:px-6">
      <div className="flex items-center gap-3">
        <button className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden" onClick={onMenu} aria-label="Open navigation"><Menu className="h-5 w-5" /></button>
        <div><p className="text-xs font-semibold uppercase tracking-[0.18em] text-brand-500">Private workspace</p><h1 className="text-base font-bold text-slate-950 dark:text-white">{routeTitles[pathname] ?? "Company Assistant"}</h1></div>
      </div>
      <div className="flex items-center gap-2">
        <button className="hidden rounded-xl p-2.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 sm:block" aria-label="Search"><Search className="h-5 w-5" /></button>
        <button className="relative rounded-xl p-2.5 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800" aria-label="Notifications"><Bell className="h-5 w-5" /><span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-brand-500" /></button>
        <div className="ml-1 flex h-9 w-9 items-center justify-center rounded-full bg-brand-50 text-xs font-bold text-brand-600 dark:bg-brand-500/20 dark:text-indigo-200" title={currentUser.name}>{currentUser.name.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div>
      </div>
    </header>
  );
}
