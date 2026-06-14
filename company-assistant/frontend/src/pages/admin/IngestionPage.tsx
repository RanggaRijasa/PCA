import {
  AlertTriangle,
  CheckCircle2,
  FileUp,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  ShieldCheck,
  UploadCloud,
} from "lucide-react";
import { type FormEvent, useCallback, useEffect, useState } from "react";
import { Badge } from "../../components/common/Badge";
import { Button } from "../../components/common/Button";
import { PageHeader } from "../../components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "../../components/common/States";
import { useToast } from "../../context/ToastContext";
import {
  listIngestionJobs,
  runAdminIngestion,
  uploadAdminDocument,
} from "../../services/adminApi";
import type { AccessLevel, IngestionJob } from "../../types";

const fieldClass =
  "mt-1.5 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-white";

const activeStatuses = new Set(["validating", "extracting", "chunking", "embedding", "indexing"]);

export function IngestionPage() {
  const { showToast } = useToast();
  const [jobs, setJobs] = useState<IngestionJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [runningJobId, setRunningJobId] = useState<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [form, setForm] = useState({
    title: "",
    department: "",
    accessLevel: "staff" as AccessLevel,
    owner: "",
    version: "1.0",
    effectiveDate: "",
    expiryDate: "",
    documentType: "policy",
  });

  const loadJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setJobs(await listIngestionJobs());
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Could not load ingestion jobs.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadJobs();
  }, [loadJobs]);

  const updateField = (name: keyof typeof form, value: string) => {
    setForm((current) => ({ ...current, [name]: value }));
  };

  const submitUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF, DOCX, TXT, or Markdown file first.");
      return;
    }
    setUploading(true);
    setError(null);
    try {
      await uploadAdminDocument({ file, ...form });
      showToast("Upload validated and queued for approval.");
      setFile(null);
      setForm((current) => ({ ...current, title: "", version: "1.0", expiryDate: "" }));
      event.currentTarget.reset();
      await loadJobs();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  };

  const runJob = async (job: IngestionJob) => {
    setRunningJobId(job.id);
    setError(null);
    try {
      let result: Awaited<ReturnType<typeof runAdminIngestion>>;
      if (job.status === "queued") {
        result = await runAdminIngestion({ jobId: job.id });
      } else if (job.documentVersionId) {
        result = await runAdminIngestion({ documentVersionId: job.documentVersionId, reindex: true });
      } else {
        throw new Error("This historical job is not linked to a document version.");
      }
      if (result.job.status === "failed") {
        throw new Error(result.job.errorMessage || "Ingestion failed. Review the job details and retry.");
      }
      showToast(job.status === "queued" ? "Document approved and indexing finished." : "Re-indexing finished.");
      await loadJobs();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Ingestion failed.");
      await loadJobs();
    } finally {
      setRunningJobId(null);
    }
  };

  return (
    <div className="p-5 sm:p-7">
      <PageHeader
        title="Ingestion queue"
        description="Validate and stage documents, then explicitly approve them before local indexing."
        actions={
          <Button variant="secondary" onClick={() => void loadJobs()} disabled={loading}>
            <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
            Refresh queue
          </Button>
        }
      />

      {error && <div className="mb-5"><ErrorState message={error} /></div>}

      <form onSubmit={submitUpload} className="grid gap-5 xl:grid-cols-[1fr_420px]">
        <section className="rounded-2xl border border-dashed border-slate-300 bg-white p-8 dark:border-slate-700 dark:bg-slate-900">
          <div className="flex flex-col items-center text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-50 text-brand-600 dark:bg-brand-500/20 dark:text-indigo-200">
              <UploadCloud className="h-6 w-6" />
            </div>
            <h2 className="mt-4 font-bold text-slate-950 dark:text-white">Upload an approved company document</h2>
            <p className="mx-auto mt-2 max-w-lg text-sm leading-6 text-slate-500">
              Uploading only creates a staged version. It remains outside search until an administrator chooses Approve and index and the job completes.
            </p>
            <label className="mt-5 inline-flex cursor-pointer items-center gap-2 rounded-xl bg-brand-500 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-600">
              <FileUp className="h-4 w-4" />
              Choose file
              <input
                className="sr-only"
                type="file"
                accept=".pdf,.docx,.txt,.md"
                required
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </label>
            <p className="mt-3 text-sm font-medium text-slate-700 dark:text-slate-200">
              {file ? `${file.name} · ${formatBytes(file.size)}` : "PDF, DOCX, TXT, or MD"}
            </p>
            <div className="mt-6 flex items-start gap-3 rounded-xl bg-amber-50 p-4 text-left text-sm text-amber-900 dark:bg-amber-950/30 dark:text-amber-200">
              <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0" />
              <span>File type, content signature, size, SHA256 hash, and required metadata are validated before the upload is queued.</span>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
          <h2 className="font-bold text-slate-950 dark:text-white">Required metadata</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
            <Field label="Title"><input required className={fieldClass} value={form.title} onChange={(event) => updateField("title", event.target.value)} /></Field>
            <Field label="Department"><input required className={fieldClass} value={form.department} onChange={(event) => updateField("department", event.target.value)} /></Field>
            <Field label="Access level">
              <select className={fieldClass} value={form.accessLevel} onChange={(event) => updateField("accessLevel", event.target.value)}>
                {(["public_internal", "staff", "manager", "admin", "restricted"] as AccessLevel[]).map((level) => <option key={level}>{level}</option>)}
              </select>
            </Field>
            <Field label="Owner"><input required className={fieldClass} value={form.owner} onChange={(event) => updateField("owner", event.target.value)} /></Field>
            <Field label="Version"><input required className={fieldClass} value={form.version} onChange={(event) => updateField("version", event.target.value)} /></Field>
            <Field label="Document type">
              <select className={fieldClass} value={form.documentType} onChange={(event) => updateField("documentType", event.target.value)}>
                {["policy", "sop", "manual", "faq", "report", "other"].map((type) => <option key={type}>{type}</option>)}
              </select>
            </Field>
            <Field label="Effective date"><input required type="date" className={fieldClass} value={form.effectiveDate} onChange={(event) => updateField("effectiveDate", event.target.value)} /></Field>
            <Field label="Expiry date (optional)"><input type="date" className={fieldClass} value={form.expiryDate} onChange={(event) => updateField("expiryDate", event.target.value)} /></Field>
          </div>
          <Button className="mt-5 w-full" type="submit" disabled={uploading}>
            {uploading ? <LoaderCircle className="h-4 w-4 animate-spin" /> : <UploadCloud className="h-4 w-4" />}
            {uploading ? "Validating upload..." : "Validate and queue"}
          </Button>
        </section>
      </form>

      <section className="mt-5 overflow-hidden rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b border-slate-200 p-5 dark:border-slate-800">
          <h2 className="font-bold text-slate-950 dark:text-white">Ingestion jobs</h2>
          <p className="mt-1 text-sm text-slate-500">Failed jobs retain their error and can be retried. Completed current versions can be re-indexed.</p>
        </div>
        {loading ? <LoadingState label="Loading ingestion queue..." /> : jobs.length === 0 ? (
          <div className="p-5"><EmptyState title="No ingestion jobs" description="Validated uploads will appear here before they become searchable." /></div>
        ) : (
          <div className="divide-y divide-slate-100 dark:divide-slate-800">
            {jobs.map((job) => {
              const running = runningJobId === job.id || activeStatuses.has(job.status);
              const hasVersion = Boolean(job.documentVersionId);
              const canRun = hasVersion && (job.status === "queued" || job.status === "failed" || (job.status === "completed" && job.isCurrentVersion));
              return (
                <article key={job.id} className="p-5">
                  <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-center">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="truncate font-semibold text-slate-900 dark:text-white">{job.title}</h3>
                        <Badge tone={jobTone(job.status)}>{job.status}</Badge>
                        {!job.isCurrentVersion && job.status === "completed" && <Badge>superseded</Badge>}
                      </div>
                      <p className="mt-1 text-xs text-slate-500">{job.sourceFile} · version {job.version} · {job.department} · {job.accessLevel}</p>
                      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">{job.currentStep}</p>
                      {job.errorMessage && (
                        <p className="mt-2 flex items-start gap-2 text-sm text-red-700 dark:text-red-300"><AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />{job.errorMessage}</p>
                      )}
                      <p className="mt-2 text-xs text-slate-400">Queued {formatDate(job.createdAt)} · {formatBytes(job.fileSizeBytes)}</p>
                    </div>
                    {canRun && (
                      <Button variant={job.status === "queued" ? "primary" : "secondary"} disabled={runningJobId !== null || running} onClick={() => void runJob(job)}>
                        {running ? <LoaderCircle className="h-4 w-4 animate-spin" /> : job.status === "queued" ? <CheckCircle2 className="h-4 w-4" /> : <RotateCcw className="h-4 w-4" />}
                        {job.status === "queued" ? "Approve and index" : job.status === "failed" ? "Retry indexing" : "Re-index"}
                      </Button>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </section>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="text-xs font-semibold text-slate-500">{label}{children}</label>;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(value: string): string {
  const normalized = value.includes("T") ? value : `${value.replace(" ", "T")}Z`;
  return new Intl.DateTimeFormat("en", { dateStyle: "medium", timeStyle: "short" }).format(new Date(normalized));
}

function jobTone(status: IngestionJob["status"]): "slate" | "green" | "amber" | "red" | "purple" {
  if (status === "completed") return "green";
  if (status === "failed") return "red";
  if (status === "queued") return "amber";
  if (status === "archived") return "slate";
  return "purple";
}
