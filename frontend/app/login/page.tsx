"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Shell, Sidebar, Card } from "@/components/ui";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      if (mode === "login") {
        const result = await api.login(email, password);
        setToken(result.access_token);
        router.push("/");
      } else {
        await api.register(email, password, displayName || undefined);
        const result = await api.login(email, password);
        setToken(result.access_token);
        router.push("/");
      }
    } catch (err: any) {
      setError(err.message || "操作失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Shell>
      <Sidebar />
      <main className="flex-1">
        <Card title={mode === "login" ? "登录" : "注册"} subtitle="JWT 认证入口">
          <form onSubmit={handleSubmit} className="grid gap-4 md:max-w-md">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setMode("login")}
                className={`flex-1 rounded-xl px-4 py-2 text-sm transition ${
                  mode === "login"
                    ? "bg-accent text-slate-950"
                    : "border border-white/10 bg-white/5 text-muted hover:bg-white/10"
                }`}
              >
                登录
              </button>
              <button
                type="button"
                onClick={() => setMode("register")}
                className={`flex-1 rounded-xl px-4 py-2 text-sm transition ${
                  mode === "register"
                    ? "bg-accent text-slate-950"
                    : "border border-white/10 bg-white/5 text-muted hover:bg-white/10"
                }`}
              >
                注册
              </button>
            </div>

            <input
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
              placeholder="邮箱"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            {mode === "register" && (
              <input
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
                placeholder="显示名称（可选）"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
              />
            )}

            <input
              className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 outline-none"
              placeholder="密码"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            {error && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="rounded-xl bg-accent px-4 py-3 font-medium text-slate-950 transition hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "处理中..." : mode === "login" ? "登录" : "注册"}
            </button>
          </form>

          <div className="mt-4 text-sm text-muted">
            <p>默认管理员账号：</p>
            <p>邮箱：admin@example.com</p>
            <p>密码：Admin123!</p>
          </div>
        </Card>
      </main>
    </Shell>
  );
}
