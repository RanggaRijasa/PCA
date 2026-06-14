import { LockKeyhole } from "lucide-react";
import { Badge } from "../../components/common/Badge";
import { PageHeader } from "../../components/common/PageHeader";

const groups = [
  { title: "Model settings", fields: [["LLM model", "Not configured in Phase 0-2"], ["Embedding model", "Not configured in Phase 0-2"]] },
  { title: "Retrieval settings", fields: [["Initial top-k", "20"], ["Rerank top-n", "5"], ["Max context chunks", "6"]] },
  { title: "Security settings", fields: [["Audit logging", "Mock only"], ["Authentication", "Not implemented"], ["Permission retrieval", "Not implemented"]] },
  { title: "Local operations", fields: [["Max upload size", "Not configured"], ["Allowed files", "PDF, DOCX, TXT, MD"], ["Backup schedule", "Not configured"]] },
];

export function SettingsPage() {
  return <div className="p-5 sm:p-7"><PageHeader title="Settings" description="Read-only configuration preview. Runtime values will come from .env in later phases." actions={<Badge tone="purple"><LockKeyhole className="mr-1 h-3 w-3" />Read only</Badge>} /><div className="grid gap-5 xl:grid-cols-2">{groups.map((group) => <section key={group.title} className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900"><h2 className="font-bold text-slate-950 dark:text-white">{group.title}</h2><div className="mt-4 space-y-3">{group.fields.map(([label, value]) => <label key={label} className="block text-xs font-semibold text-slate-500">{label}<input readOnly value={value} className="mt-1.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm font-medium text-slate-700 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200" /></label>)}</div></section>)}</div></div>;
}

