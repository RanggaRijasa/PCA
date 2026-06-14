import { BookOpen, LockKeyhole } from "lucide-react";
import { type FormEvent, useState } from "react";
import { Button } from "../components/common/Button";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, isLoading, error } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await login(username, password);
    } catch {
      // The context exposes the intentionally generic authentication error.
    }
  };

  return <main className="flex min-h-screen items-center justify-center bg-slate-100 px-5 dark:bg-slate-950"><section className="w-full max-w-md rounded-3xl border border-slate-200 bg-white p-8 shadow-xl shadow-slate-200/40 dark:border-slate-800 dark:bg-slate-900 dark:shadow-none"><div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-brand-500 text-white"><BookOpen className="h-6 w-6" /></div><h1 className="mt-6 text-2xl font-bold text-slate-950 dark:text-white">Sign in to Company AI</h1><p className="mt-2 text-sm leading-6 text-slate-500">Use your local company account. Authentication and document permissions are enforced by the backend.</p><form className="mt-7 space-y-5" onSubmit={(event) => void submit(event)}><div><label htmlFor="username" className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Username or email</label><input id="username" autoComplete="username" required value={username} onChange={(event) => setUsername(event.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-950" /></div><div><label htmlFor="password" className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Password</label><input id="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-3 text-sm outline-none ring-brand-500 focus:ring-2 dark:border-slate-700 dark:bg-slate-950" /></div>{error && <div role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950/30 dark:text-red-200">{error}</div>}<Button type="submit" className="w-full justify-center" disabled={isLoading}><LockKeyhole className="h-4 w-4" />{isLoading ? "Signing in..." : "Sign in"}</Button></form><p className="mt-6 text-center text-xs text-slate-400">Local-first authentication. Credentials never leave this machine.</p></section></main>;
}
