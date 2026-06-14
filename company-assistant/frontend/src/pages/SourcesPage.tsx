import { Search } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { DocumentTable } from "../components/admin/DocumentTable";
import { PageHeader } from "../components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../components/common/States";
import { listDocuments } from "../services/documentsApi";
import type { DocumentSource } from "../types";

export function SourcesPage() {
  const [documents, setDocuments] = useState<DocumentSource[]>([]);
  const [query, setQuery] = useState("");
  const [department, setDepartment] = useState("all");
  const [status, setStatus] = useState("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listDocuments()
      .then(setDocuments)
      .catch((caught: Error) => setError(caught.message))
      .finally(() => setLoading(false));
  }, []);

  const departments = useMemo(
    () => [...new Set(documents.map((item) => item.department))].sort(),
    [documents],
  );
  const filtered = useMemo(
    () => documents.filter((item) =>
      item.title.toLowerCase().includes(query.toLowerCase())
      && (department === "all" || item.department === department)
      && (status === "all" || item.status === status)),
    [documents, query, department, status],
  );

  return (
    <div className="p-5 sm:p-7">
      <PageHeader
        title="Knowledge sources"
        description="Browse indexed and staged local knowledge available to your role."
      />
      <div className="mb-5 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900 md:grid-cols-[1fr_180px_180px]">
        <div className="relative">
          <label className="sr-only" htmlFor="source-search">Search sources</label>
          <Search className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
          <input
            id="source-search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search by title"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm outline-none focus:border-brand-500 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          />
        </div>
        <select
          value={department}
          onChange={(event) => setDepartment(event.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          aria-label="Filter by department"
        >
          <option value="all">All departments</option>
          {departments.map((item) => <option key={item} value={item}>{item}</option>)}
        </select>
        <select
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-950 dark:text-white"
          aria-label="Filter by status"
        >
          <option value="all">All statuses</option>
          <option value="indexed">Indexed</option>
          <option value="approved">Approved</option>
          <option value="indexing">Indexing</option>
          <option value="pending_ingestion">Pending ingestion</option>
          <option value="failed">Failed</option>
          <option value="archived">Archived</option>
        </select>
      </div>
      {loading ? (
        <LoadingState />
      ) : error ? (
        <ErrorState message={error} onRetry={() => window.location.reload()} />
      ) : filtered.length ? (
        <DocumentTable documents={filtered} showActions={false} />
      ) : (
        <EmptyState title="No sources match" description="Try changing the search text or filters." />
      )}
    </div>
  );
}
