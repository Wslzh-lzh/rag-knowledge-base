"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight, Lock, Mail, Sparkles, User } from "lucide-react";

import { api, setToken } from "@/lib/api";

function FloatingParticles() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute top-[10%] left-[10%] h-64 w-64 animate-float rounded-full bg-primary/20 blur-3xl" />
      <div
        className="absolute top-[20%] right-[15%] h-96 w-96 animate-float-slow rounded-full bg-secondary/15 blur-3xl"
        style={{ animationDelay: "1s" }}
      />
      <div
        className="absolute bottom-[15%] left-[30%] h-80 w-80 animate-float rounded-full bg-accent/10 blur-3xl"
        style={{ animationDelay: "2s" }}
      />
      <div
        className="absolute right-[25%] bottom-[25%] h-56 w-56 animate-float-slow rounded-full bg-accent-blue/15 blur-3xl"
        style={{ animationDelay: "0.5s" }}
      />
    </div>
  );
}

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
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden p-6">
      <div className="grid-bg absolute inset-0 opacity-20" />
      <FloatingParticles />

      <div className="relative z-10 w-full max-w-md animate-fade-in-up">
        <div className="mb-8 text-center">
          <div className="glow-effect mb-4 inline-flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-secondary">
            <Sparkles className="h-8 w-8 text-white" />
          </div>
          <h1 className="mb-2 text-4xl font-bold">
            <span className="gradient-text-primary">RAG</span>
            <span className="text-white"> Platform</span>
          </h1>
          <p className="text-muted">智能知识库问答平台</p>
        </div>

        <div className="gradient-border rounded-3xl glass p-8 shadow-glass">
          <div className="mb-6 flex gap-2 rounded-2xl bg-white/5 p-1">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`flex-1 rounded-xl py-2.5 text-sm font-medium transition-all duration-300 ${
                mode === "login"
                  ? "bg-gradient-to-r from-primary to-secondary text-white shadow-lg shadow-primary/25"
                  : "text-muted hover:text-text"
              }`}
            >
              登录
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`flex-1 rounded-xl py-2.5 text-sm font-medium transition-all duration-300 ${
                mode === "register"
                  ? "bg-gradient-to-r from-primary to-secondary text-white shadow-lg shadow-primary/25"
                  : "text-muted hover:text-text"
              }`}
            >
              注册
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="group relative">
              <Mail className="absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 text-muted transition-colors group-focus-within:text-primary" />
              <input
                className="input-glow w-full rounded-xl border border-glass-border bg-white/5 py-3.5 pr-4 pl-12 text-text outline-none transition-all duration-300 placeholder:text-muted focus:border-primary/50 focus:bg-white/10"
                placeholder="邮箱地址"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {mode === "register" && (
              <div className="group relative">
                <User className="absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 text-muted transition-colors group-focus-within:text-primary" />
                <input
                  className="input-glow w-full rounded-xl border border-glass-border bg-white/5 py-3.5 pr-4 pl-12 text-text outline-none transition-all duration-300 placeholder:text-muted focus:border-primary/50 focus:bg-white/10"
                  placeholder="显示名称（可选）"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
              </div>
            )}

            <div className="group relative">
              <Lock className="absolute top-1/2 left-4 h-5 w-5 -translate-y-1/2 text-muted transition-colors group-focus-within:text-primary" />
              <input
                className="input-glow w-full rounded-xl border border-glass-border bg-white/5 py-3.5 pr-4 pl-12 text-text outline-none transition-all duration-300 placeholder:text-muted focus:border-primary/50 focus:bg-white/10"
                placeholder="密码"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="animate-fade-in rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="btn-gradient group flex w-full items-center justify-center gap-2 rounded-xl py-3.5 font-medium text-white"
            >
              {loading ? (
                <>
                  <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  处理中...
                </>
              ) : (
                <>
                  {mode === "login" ? "登录" : "注册"}
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 rounded-xl border border-amber-500/20 bg-gradient-to-r from-amber-500/10 to-orange-500/5 p-4">
            <p className="mb-1 flex items-center gap-1.5 text-xs font-medium text-amber-400">
              <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
              体验账号
            </p>
            <div className="space-y-0.5 text-xs text-muted">
              <p>邮箱：admin@example.com</p>
              <p>密码：Admin123!</p>
            </div>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-muted">© 2025 RAG Platform. All rights reserved.</p>
      </div>
    </div>
  );
}
