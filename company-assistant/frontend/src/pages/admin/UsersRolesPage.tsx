import { UserCog } from "lucide-react";
import { Badge } from "../../components/common/Badge";
import { PageHeader } from "../../components/common/PageHeader";
import { mockUsers } from "../../mocks/users";

export function UsersRolesPage() {
  return <div className="p-5 sm:p-7"><PageHeader title="Users & roles" description="Mock role directory for UI visibility testing. No real authentication or authorization is implemented." /><div className="overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900"><div className="overflow-x-auto"><table className="w-full min-w-[760px] text-left text-sm"><thead className="bg-slate-50 text-[11px] uppercase tracking-[0.12em] text-slate-500 dark:bg-slate-950"><tr>{["User", "Role", "Department", "Status", "Last active", "Access details"].map((label) => <th key={label} className="px-5 py-3 font-bold">{label}</th>)}</tr></thead><tbody className="divide-y divide-slate-100 dark:divide-slate-800">{mockUsers.map((user, index) => <tr key={user.id}><td className="px-5 py-4"><p className="font-semibold text-slate-950 dark:text-white">{user.name}</p><p className="text-xs text-slate-400">{user.email}</p></td><td className="px-5 py-4"><Badge tone={user.role === "admin" ? "purple" : "slate"}>{user.role}</Badge></td><td className="px-5 py-4 text-slate-600 dark:text-slate-300">{user.department}</td><td className="px-5 py-4"><Badge tone="green">{user.status}</Badge></td><td className="px-5 py-4 text-slate-500">{index === 0 ? "Just now" : `${index + 1} hours ago`}</td><td className="px-5 py-4"><button disabled className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-300"><UserCog className="h-4 w-4" />Manage later</button></td></tr>)}</tbody></table></div></div></div>;
}

