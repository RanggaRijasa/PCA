import { BarChart3, BookOpen, Bot, Database, FileSearch, FileText, LogOut, Moon, Settings, ShieldCheck, Sun, UploadCloud, Users, X } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth, useAuthenticatedUser } from "../../context/AuthContext";
import { useTheme } from "../../context/ThemeContext";
import type { UserRole } from "../../types";

type NavItem = { label: string; path: string; icon: LucideIcon; minimumRole?: UserRole; adminOnly?: boolean };
const roleRank: Record<UserRole, number> = { viewer: 0, staff: 1, manager: 2, admin: 3 };

const mainItems: NavItem[] = [
  { label: "Chat", path: "/chat", icon: Bot },
  { label: "Sources", path: "/sources", icon: FileSearch },
  { label: "Documents", path: "/documents", icon: FileText },
  { label: "Reports", path: "/reports", icon: BarChart3, minimumRole: "staff" },
];
const adminItems: NavItem[] = [
  { label: "Ingestion", path: "/admin/ingestion", icon: UploadCloud, adminOnly: true },
  { label: "Users & Roles", path: "/admin/users", icon: Users, adminOnly: true },
  { label: "Audit Logs", path: "/admin/audit-logs", icon: ShieldCheck, adminOnly: true },
  { label: "Evaluation", path: "/admin/evaluation", icon: Database, adminOnly: true },
  { label: "Settings", path: "/admin/settings", icon: Settings, adminOnly: true },
];

export function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const currentUser = useAuthenticatedUser();
  const { logout } = useAuth();
  const { darkMode, toggleDarkMode } = useTheme();
  const visibleMain = mainItems.filter((item) => !item.minimumRole || roleRank[currentUser.role] >= roleRank[item.minimumRole]);

  const nav = (items: NavItem[]) => items.map(({ label, path, icon: Icon }) => (
    <NavLink key={path} to={path} onClick={onClose} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${isActive ? "bg-white/12 text-white" : "text-slate-300 hover:bg-white/7 hover:text-white"}`}>
      <Icon className="h-[18px] w-[18px]" />{label}
    </NavLink>
  ));

  return (
    <>
      {open && <button className="fixed inset-0 z-30 bg-slate-950/50 lg:hidden" onClick={onClose} aria-label="Close navigation overlay" />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-60 flex-col bg-navy-950 text-white transition-transform lg:static lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex h-16 items-center justify-between border-b border-white/10 px-5"><div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-500"><BookOpen className="h-5 w-5" /></div><div><p className="text-sm font-bold">Company AI</p><p className="text-[11px] text-slate-400">Local knowledge desk</p></div></div><button className="p-1 lg:hidden" onClick={onClose} aria-label="Close navigation"><X className="h-5 w-5" /></button></div>
        <nav className="flex-1 space-y-6 overflow-y-auto p-4" aria-label="Primary navigation"><div><p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Workspace</p><div className="space-y-1">{nav(visibleMain)}</div></div>{currentUser.role === "admin" && <div><p className="mb-2 px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Administration</p><div className="space-y-1">{nav(adminItems)}</div></div>}</nav>
        <div className="border-t border-white/10 p-4">
          <div className="flex items-center gap-3"><div className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 text-xs font-bold">{currentUser.name.split(" ").map((part) => part[0]).slice(0, 2).join("")}</div><div className="min-w-0 flex-1"><p className="truncate text-xs font-semibold">{currentUser.name}</p><p className="truncate text-[11px] capitalize text-slate-400">{currentUser.role} · {currentUser.department}</p></div></div>
          <button onClick={toggleDarkMode} className="mt-4 flex w-full items-center justify-between rounded-xl bg-white/5 px-3 py-2.5 text-xs text-slate-300 hover:bg-white/10"><span className="flex items-center gap-2">{darkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}{darkMode ? "Light mode" : "Dark mode"}</span><span className="text-[10px] text-slate-500">v0.13</span></button>
          <button onClick={() => void logout()} className="mt-2 flex w-full items-center gap-2 rounded-xl px-3 py-2.5 text-xs text-slate-300 hover:bg-white/10"><LogOut className="h-4 w-4" />Sign out</button>
        </div>
      </aside>
    </>
  );
}
