"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { LucideIcon } from "lucide-react";
import { LogOut } from "lucide-react";
import { useEffect, useState } from "react";

import { navItems } from "@/lib/nav";
import { api, clearToken, getToken } from "@/lib/api";
import type { UserProfile } from "@/lib/api";

export function Shell({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto flex min-h-screen max-w-7xl gap-6 p-6">{children}</div>;
}

export function Sidebar() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);

  useEffect(() => {
    if (!getToken()) return;
    api.me().then(setUser).catch(() => clearToken());
  }, []);

  function handleLogout() {
    clearToken();
    router.push("/login");
  }

  return (
    <aside className="w-64 shrink-0 flex flex-col rounded-2xl border border-white/10 bg-panel/90 p-4 shadow-soft backdrop-blur">
      <div className="mb-6">
        <div className="text-xs uppercase tracking-[0.25em] text-muted">RAG Platform</div>
        <div className="mt-2 text-2xl font-semibold">知识库问答</div>
      </div>
      <nav className="space-y-2 flex-1">
        {navItems.map((item) => {
          const Icon = item.icon as LucideIcon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="flex items-center gap-3 rounded-xl border border-transparent px-3 py-2 text-sm text-text transition hover:border-white/10 hover:bg-white/5"
            >
              <Icon className="h-4 w-4 text-accent" />
              {item.label}
            </Link>
          );
        })}
      </nav>
      {user && (
        <div className="mt-4 pt-4 border-t border-white/10">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-medium">{user.display_name || user.email}</div>
              <div className="text-xs text-muted">{user.role}</div>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-lg p-2 text-muted transition hover:bg-white/5 hover:text-text"
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
  children
}: {
  title: string;
  subtitle?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-2xl border border-white/10 bg-panel/80 p-5 shadow-soft">
      <div className="mb-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
      </div>
      {children}
    </section>
  );
}

export function Stat({
  label,
  value
}: {
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
      <div className="mt-2 text-2xl font-semibold">{value}</div>
    </div>
  );
}
