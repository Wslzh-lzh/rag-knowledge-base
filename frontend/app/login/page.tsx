"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Mail, Lock, User, ArrowRight } from "lucide-react";
import { api, setToken } from "@/lib/api";

function FloatingParticles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      <div className="absolute top-[10%] left-[10%] w-64 h-64 bg-primary/20 rounded-full blur-3xl animate-float" />
      <div className="absolute top-[20%] right-[15%] w-96 h-96 bg-secondary/15 rounded-full blur-3xl animate-float-slow" style={{ animationDelay: "1s" }} />
      <div className="absolute bottom-[15%] left-[30%] w-80 h-80 bg-accent/10 rounded-full blur-3xl animate-float" style={{ animationDelay: "2s" }} />
      <div className="absolute bottom-[25%] right-[25%] w-56 h-56 bg-accent-blue/15 rounded-full blur-3xl animate-float-slow" style={{ animationDelay: "0.5s" }} />
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
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
      <div className="grid-bg absolute inset-0 opacity-20" />
      <FloatingParticles />

      <div className="relative w-full max-w-md z-10 animate-fade-in-up">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-primary to-secondary mb-4 glow-effect">
            <Sparkles className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-4xl font-bold mb-2">
            <span className="gradient-text-primary">RAG</span>
            <span className="text-white"> Platform</span>
          </h1>
          <p className="text-muted">智能知识库问答平台</p>
        </div>

        <div className="glass rounded-3xl shadow-glass p-8 gradient-border">
          <div className="flex gap-2 mb-6 p-1 bg-white/5 rounded-2xl">
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
            <div className="relative group">
              <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted group-focus-within:text-primary transition-colors" />
              <input
                className="w-full rounded-xl border border-glass-border bg-white/5 pl-12 pr-4 py-3.5 outline-none transition-all duration-300 focus:border-primary/50 focus:bg-white/10 input-glow text-text placeholder:text-muted"
                placeholder="邮箱地址"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {mode === "register" && (
              <div className="relative group">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted group-focus-within:text-primary transition-colors" />
                <input
                  className="w-full rounded-xl border border-glass-border bg-white/5 pl-12 pr-4 py-3.5 outline-none transition-all duration-300 focus:border-primary/50 focus:bg-white/10 input-glow text-text placeholder:text-muted"
                  placeholder="显示名称（可选）"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                />
              </div>
            )}

            <div className="relative group">
              <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted group-focus-within:text-primary transition-colors" />
              <input
                className="w-full rounded-xl border border-glass-border bg-white/5 pl-12 pr-4 py-3.5 outline-none transition-all duration-300 focus:border-primary/50 focus:bg-white/10 input-glow text-text placeholder:text-muted"
                placeholder="密码"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400 animate-fade-in">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full btn-gradient rounded-xl py-3.5 font-medium text-white flex items-center justify-center gap-2 group"
            >
              {loading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  处理中...
                </>
              ) : (
                <>
                  {mode === "login" ? "登录" : "注册"}
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                </>
              )}
            </button>
          </form>

          <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-amber-500/10 to-orange-500/5 border border-amber-500/20">
            <p className="text-xs text-amber-400 font-medium mb-1 flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
              体验账号
            </p>
            <div className="text-xs text-muted space-y-0.5">
              <p>邮箱：admin@example.com</p>
              <p>密码：Admin123!</p>
            </div>
          </div>
        </div>

        <p className="text-center text-xs text-muted mt-6">
          © 2025 RAG Platform. All rights reserved.
        </p>
      </div>
    </div>
  );
}
