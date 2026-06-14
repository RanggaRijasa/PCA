import { type ReactNode, useState } from "react";
import { Sidebar } from "./Sidebar";
import { TopBar } from "./TopBar";

export function AppShell({ children }: { children: ReactNode }) {
  const [menuOpen, setMenuOpen] = useState(false);
  return <div className="flex h-screen overflow-hidden bg-slate-100 dark:bg-slate-950"><Sidebar open={menuOpen} onClose={() => setMenuOpen(false)} /><div className="flex min-w-0 flex-1 flex-col"><TopBar onMenu={() => setMenuOpen(true)} /><main className="min-h-0 flex-1 overflow-auto">{children}</main></div></div>;
}

