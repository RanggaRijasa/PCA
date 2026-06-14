import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: "primary" | "secondary" | "ghost" | "danger";
};

const variants = {
  primary: "bg-brand-500 text-white hover:bg-brand-600 shadow-sm",
  secondary: "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800",
  ghost: "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
  danger: "bg-red-50 text-red-700 hover:bg-red-100 dark:bg-red-950/40 dark:text-red-300",
};

export function Button({ children, className = "", variant = "primary", ...props }: ButtonProps) {
  return <button className={`inline-flex items-center justify-center gap-2 rounded-xl px-3.5 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${variants[variant]} ${className}`} {...props}>{children}</button>;
}

