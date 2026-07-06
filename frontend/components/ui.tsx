"use client";

import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { LogOut, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";

import { navItems } from "@/lib/nav";
import { api, clearToken, getToken } from "@/lib/api";
import type { UserProfile } from "@/lib/api";

export function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen">
      <div className="grid-bg fixed inset-0 opacity-30 pointer-events-none" />
      <div className="relative mx-auto flex min-h-screen max-w-7xl gap-6 p-6">
        {children}
      </div>
    </div>
  );
}

export function Sidebar() {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    if (!getToken()) return;
    api.me().then(setUser).catch(() => clearToken());
  }, []);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  function getUserInitials(email: string) {
    return email
      .split("@")[0]
      .split(/[._-]/)
      .map((s) => s[0]?.toUpperCase() || "")
      .join("")
      .slice(0, 2);
  }

  return (
    <aside className="w-64 shrink-0 flex flex-col rounded-2xl glass shadow-glass overflow-hidden">
      <div className="mb-6 p-4 pb-2">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary to-secondary flex items-center justify-center">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="text-xs uppercase tracking-[0.25em] text-muted">RAG Platform</span>
        </div>
        <div className="text-2xl font-semibold gradient-text-primary">知识库问答</div>
      </div>
      <nav className="space-y-1 flex-1 px-3">
        {navItems.map((item) => {
          const Icon = item.icon as LucideIcon;
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`relative flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-text transition-all duration-300 ${
                isActive
                  ? "bg-gradient-to-r from-primary/20 to-secondary/10 text-white"
                  : "hover:bg-white/5 text-muted hover:text-text"
              }`}
            >
              {isActive && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-gradient-to-b from-primary to-secondary rounded-r-full" />
              )}
              <Icon className={`h-4 w-4 ${isActive ? "text-accent-blue" : "text-primary"}`} />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      {user && (
        <div className="mt-4 pt-4 border-t border-glass-border px-3 pb-3">
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-secondary flex items-center justify-center text-white font-semibold text-sm shrink-0 glow-effect">
                {getUserInitials(user.email)}
              </div>
              <div className="min-w-0">
                <div className="text-sm font-medium truncate">{user.display_name || user.email}</div>
                <div className="text-xs text-muted capitalize">{user.role}</div>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-2 text-muted transition-all duration-200 hover:bg-white/5 hover:text-error shrink-0"
              title="登出"
            >
              <LogOut className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </aside>
  );
}

export function Card({
  title,
  subtitle,
  action,
  children
}: {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl glass shadow-glass card-hover overflow-hidden">
      <div className="p-5 border-b border-glass-border/50">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold">{title}</h2>
            {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
          </div>
          {action}
        </div>
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

export function Stat({
  label,
  value,
  icon,
  trend,
  color = "primary"
}: {
  label: string;
  value: string;
  icon?: LucideIcon;
  trend?: { value: string; positive: boolean };
  color?: "primary" | "accent" | "success" | "error";
}) {
  const colorClasses = {
    primary: "from-primary/20 to-secondary/10 text-primary",
    accent: "from-amber-500/20 to-orange-500/10 text-amber-400",
    success: "from-emerald-500/20 to-teal-500/10 text-emerald-400",
    error: "from-red-500/20 to-rose-500/10 text-red-400"
  };

  const Icon = icon;

  return (
    <div className="rounded-xl glass card-hover p-5 overflow-hidden relative">
      <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-primary/5 to-transparent rounded-full -mr-8 -mt-8" />
      <div className="relative">
        <div className="flex items-start justify-between">
          <div className="text-xs uppercase tracking-[0.15em] text-muted font-medium">{label}</div>
          {Icon && (
            <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${colorClasses[color]} flex items-center justify-center`}>
              <Icon className="w-5 h-5" />
            </div>
          )}
        </div>
        <div className="mt-3 text-3xl font-bold">{value}</div>
        {trend && (
          <div className={`mt-2 text-xs font-medium flex items-center gap-1 ${trend.positive ? "text-success" : "text-error"}`}>
            <span>{trend.positive ? "↑" : "↓"}</span>
            <span>{trend.value}</span>
            <span className="text-muted">较上周</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function Badge({
  children,
  variant = "default",
  pulse = false
}: {
  children: React.ReactNode;
  variant?: "default" | "success" | "warning" | "error" | "primary";
  pulse?: boolean;
}) {
  const variants = {
    default: "bg-white/10 text-text border-white/10",
    success: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/15 text-amber-400 border-amber-500/20",
    error: "bg-red-500/15 text-red-400 border-red-500/20",
    primary: "bg-primary/20 text-primary-foreground border-primary/30 text-primary"
  };

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${variants[variant]}`}>
      {pulse && (
        <span className={`w-1.5 h-1.5 rounded-full ${
          variant === "success" ? "bg-emerald-400" :
          variant === "warning" ? "bg-amber-400" :
          variant === "error" ? "bg-red-400" :
          "bg-primary"
        } ${pulse ? "status-pulse" : ""}`} />
      )}
      {children}
    </span>
  );
}
