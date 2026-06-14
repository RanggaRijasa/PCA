import { FileText, Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Badge } from "../components/common/Badge";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../components/common/States";
import { listDocuments } from "../services/documentsApi";
import type { DocumentSource } from "../types";

export function DocumentsPage() {
  const [documents, setDocuments] = useState<DocumentSource[]>([]);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<DocumentSource | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((caught: Error) => setError(caught.message))
      .finally(() => setLoading(false));
  }, []);

  const visible = useMemo(
    () => documents.filter((item) => item.title.toLowerCase().includes(query.toLowerCase())),
    [documents, query],
  );

  return (
    <div className="p-5 sm:p-7">
      <PageHeader
        title="Document library"
        description="Indexed and staged documents available to your role."
        actions={
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
            <label htmlFor="document-search" className="sr-only">Search documents</label>
            <input
              id="document-search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search documents"
              className="rounded-xl border border-slate-200 bg-white py-2.5 pl-9 pr-3 text-sm outline-none focus:border-brand-500 dark:border-slate-700 dark:bg-slate-900 dark:text-white"
            />
          </div>
        }
      />

      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      ) : visible.length ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {visible.map((document) => (
            <button
              key={document.id}
              onClick={() => setSelected(document)}
              className="rounded-2xl border border-slate-200 bg-white p-5 text-left shadow-sm transition hover:-translate-y-0.5 hover:border-brand-500/60 hover:shadow-panel dark:border-slate-800 dark:bg-slate-900"
            >
              <div className="flex items-start justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-red-50 text-red-600 dark:bg-red-950/40 dark:text-red-300">
                  <FileText className="h-5 w-5" />
                </div>
                <Badge tone={document.status === "indexed" ? "green" : document.status === "failed" ? "red" : "amber"}>
                  {document.status.replace("_", " ")}
                </Badge>
              </div>
              <h2 className="mt-4 line-clamp-2 font-bold text-slate-950 dark:text-white">{document.title}</h2>
              <p className="mt-2 text-xs text-slate-500">
                {document.department} · {document.version} · {document.chunkCount ?? 0} chunks
              </p>
              <div className="mt-4 border-t border-slate-100 pt-3 text-xs text-slate-400 dark:border-slate-800">
                Owner: {document.owner}
              </div>
            </button>
          ))}
        </div>
      ) : (
        <EmptyState title="No documents found" description="No documents available to your role match this search." />
      )}

      {selected && (
        <>
          <button
            className="fixed inset-0 z-40 bg-slate-950/40"
            onClick={() => setSelected(null)}
            aria-label="Close document details"
          />
          <aside className="fixed inset-y-0 right-0 z-50 w-full max-w-md overflow-y-auto bg-white p-6 shadow-2xl dark:bg-slate-950">
            <button onClick={() => setSelected(null)} className="mb-6 text-sm font-semibold text-brand-600">
              Close details
            </button>
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50 text-red-600">
              <FileText className="h-6 w-6" />
            </div>
            <h2 className="mt-5 text-xl font-bold text-slate-950 dark:text-white">{selected.title}</h2>
            <p className="mt-2 text-sm text-slate-500">Metadata for the current local document version.</p>
            <dl className="mt-6 space-y-4 text-sm">
              {[
                ["File", selected.fileName],
                ["Department", selected.department],
                ["Access", selected.accessLevel],
                ["Version", selected.version],
                ["Owner", selected.owner],
                ["Status", selected.status],
                ["Chunks", selected.chunkCount ?? 0],
              ].map(([label, value]) => (
                <div key={label} className="flex justify-between gap-4 border-b border-slate-100 pb-3 dark:border-slate-800">
                  <dt className="text-slate-400">{label}</dt>
                  <dd className="text-right font-semibold text-slate-800 dark:text-slate-200">{value}</dd>
                </div>
              ))}
            </dl>
            <div className="mt-8 rounded-2xl bg-slate-50 p-4 dark:bg-slate-900">
              <p className="text-xs font-bold uppercase tracking-[0.14em] text-slate-400">Version</p>
              <p className="mt-3 text-sm font-semibold text-slate-800 dark:text-slate-200">
                {selected.version} · Current local version
              </p>
            </div>
          </aside>
        </>
      )}
    </div>
  );
}
