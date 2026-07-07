"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, MessageSquare, Shield, ChevronRight, Clock, Database, Zap } from "lucide-react";

import { Shell, Sidebar, Card, Stat, Badge } from "@/components/ui";
import { api, getToken, clearToken } from "@/lib/api";
import type { Conversation, KnowledgeBase, UserProfile } from "@/lib/api";

export default function HomePage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }

    async function loadData() {
      try {
        setError(null);
        const [meResp, kbsResp, convsResp] = await Promise.all([
          api.me(),
          api.listKnowledgeBases(),
          api.listConversations(),
        ]);
        setUser(meResp);
        setKbs(kbsResp);
        setConvs(convsResp);
      } catch (err: any) {
        if (err.message?.includes("401") || err.message?.includes("403")) {
          clearToken();
          router.push("/login");
        } else {
          setError(err.message || "加载数据失败");
        }
      } finally {
        setLoading(false);
      }
    }

    void loadData();
  }, [router]);

  if (loading) {
    return (
      <Shell>
        <Sidebar />
        <main className="flex-1">
          <Card title="加载中...">
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
              <span className="ml-3 text-muted">正在加载数据...</span>
            </div>
          </Card>
        </main>
      </Shell>
    );
  }

  const totalDocs = kbs.reduce((sum, kb) => sum + ((kb as { document_count?: number }).document_count || 0), 0);

  return (
    <Shell>
      <Sidebar />
      <main className="flex-1 space-y-6">
        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400 animate-fade-in">
            {error}
          </div>
        )}

        <div className="relative overflow-hidden rounded-2xl glass p-6 shadow-glass">
          <div className="absolute top-0 right-0 -mr-32 -mt-32 h-64 w-64 rounded-full bg-gradient-to-br from-primary/10 to-transparent" />
          <div className="relative">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <div className="mb-1 text-sm text-muted">欢迎回来</div>
                <h1 className="mb-1 text-2xl font-bold">{user?.display_name || user?.email?.split("@")[0]}</h1>
                <p className="text-sm text-muted">
                  今天也来高效利用知识库 <span className="text-primary">{user?.role}</span>
                </p>
              </div>
              <div className="flex gap-2">
                <Badge variant="success" pulse>
                  系统正常
                </Badge>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Stat label="知识库" value={String(kbs.length)} icon={BookOpen} color="primary" trend={{ value: "+12%", positive: true }} />
          <Stat label="对话" value={String(convs.length)} icon={MessageSquare} color="accent" trend={{ value: "+8%", positive: true }} />
          <Stat label="文档" value={String(totalDocs)} icon={Database} color="success" trend={{ value: "+25%", positive: true }} />
          <Stat label="角色" value={user?.role || "user"} icon={Shield} color="primary" />
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card
            title="最近对话"
            subtitle="你的最近知识库问答"
            action={
              <button
                onClick={() => router.push("/chat")}
                className="flex items-center gap-1 text-sm text-primary transition-colors hover:text-primary/80"
              >
                查看全部
                <ChevronRight className="h-4 w-4" />
              </button>
            }
          >
            {convs.length === 0 ? (
              <div className="rounded-xl border border-dashed border-glass-border bg-white/5 p-8 text-center">
                <MessageSquare className="mx-auto mb-3 h-12 w-12 text-muted/50" />
                <p className="text-sm text-muted">暂无对话，点击右侧“问答”开始新的会话。</p>
              </div>
            ) : (
              <div className="space-y-2">
                {convs.slice(0, 5).map((conv, index) => (
                  <div
                    key={conv.id}
                    onClick={() => router.push("/chat")}
                    className="group flex cursor-pointer items-center gap-4 rounded-xl p-3 transition-all duration-200 hover:bg-white/5"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-secondary/10">
                      <MessageSquare className="h-5 w-5 text-primary" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">{conv.title}</div>
                      <div className="flex items-center gap-2 text-xs text-muted">
                        <Clock className="h-3 w-3" />
                        模式: {conv.mode}
                      </div>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted opacity-0 transition-opacity group-hover:opacity-100" />
                  </div>
                ))}
              </div>
            )}
          </Card>

          <Card
            title="知识库"
            subtitle="你的知识库列表"
            action={
              <button
                onClick={() => router.push("/kb")}
                className="flex items-center gap-1 text-sm text-primary transition-colors hover:text-primary/80"
              >
                查看全部
                <ChevronRight className="h-4 w-4" />
              </button>
            }
          >
            {kbs.length === 0 ? (
              <div className="rounded-xl border border-dashed border-glass-border bg-white/5 p-8 text-center">
                <BookOpen className="mx-auto mb-3 h-12 w-12 text-muted/50" />
                <p className="text-sm text-muted">暂无知识库，点击左侧“知识库”创建第一个知识库。</p>
              </div>
            ) : (
              <div className="space-y-2">
                {kbs.slice(0, 5).map((kb, index) => (
                  <div
                    key={kb.id}
                    onClick={() => router.push(`/kb/${kb.id}`)}
                    className="group flex cursor-pointer items-center gap-4 rounded-xl p-3 transition-all duration-200 hover:bg-white/5"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-emerald-500/20 to-teal-500/10">
                      <Database className="h-5 w-5 text-emerald-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">{kb.name}</div>
                      <div className="truncate text-xs text-muted">{kb.description || "暂无描述"}</div>
                    </div>
                    <Badge variant="default">{kb.visibility}</Badge>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        <Card title="快捷操作" subtitle="常用功能一键直达">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { icon: Zap, title: "快速问答", desc: "开始智能问答", color: "from-primary to-secondary", action: () => router.push("/chat") },
              { icon: BookOpen, title: "创建知识库", desc: "新建知识库", color: "from-emerald-500 to-teal-500", action: () => router.push("/kb") },
              { icon: Database, title: "上传文档", desc: "添加新文档", color: "from-amber-500 to-orange-500", action: () => router.push("/kb") },
              { icon: MessageSquare, title: "历史对话", desc: "查看聊天记录", color: "from-blue-500 to-indigo-500", action: () => router.push("/chat") },
            ].map((item, index) => {
              const Icon = item.icon;
              return (
                <button
                  key={index}
                  onClick={item.action}
                  className="group flex items-start gap-3 rounded-xl glass p-4 text-left transition-all duration-300 hover:scale-[1.02]"
                >
                  <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${item.color} shadow-lg`}>
                    <Icon className="h-6 w-6 text-white" />
                  </div>
                  <div className="min-w-0">
                    <div className="font-semibold">{item.title}</div>
                    <div className="mt-0.5 text-xs text-muted">{item.desc}</div>
                  </div>
                </button>
              );
            })}
          </div>
        </Card>
      </main>
    </Shell>
  );
}
