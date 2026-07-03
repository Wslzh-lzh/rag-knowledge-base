"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell, Sidebar, Card, Stat } from "@/components/ui";
import { api, getToken, clearToken } from "@/lib/api";
import type { KnowledgeBase, UserProfile, Conversation } from "@/lib/api";

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

    loadData();
  }, [router]);

  if (loading) {
    return (
      <Shell>
        <Sidebar />
        <main className="flex-1">
          <Card title="加载中...">
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
              <span className="ml-3 text-muted">正在加载数据...</span>
            </div>
          </Card>
        </main>
      </Shell>
    );
  }

  return (
    <Shell>
      <Sidebar />
      <main className="flex-1 space-y-6">
        {error && (
          <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
            {error}
          </div>
        )}

        <Card title="工作台" subtitle={`欢迎回来，${user?.display_name || user?.email}（${user?.role}）`}>
          <div className="grid gap-3 md:grid-cols-3">
            <Stat label="知识库" value={String(kbs.length)} />
            <Stat label="对话" value={String(convs.length)} />
            <Stat label="角色" value={user?.role || "user"} />
          </div>
        </Card>

        <Card title="最近对话" subtitle="你的最近知识库问答">
          {convs.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-sm text-muted">
              暂无对话，点击左侧「问答」开始新的对话
            </div>
          ) : (
            <div className="grid gap-3">
              {convs.slice(0, 5).map((conv) => (
                <div
                  key={conv.id}
                  onClick={() => router.push("/chat")}
                  className="rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10 cursor-pointer"
                >
                  <div className="font-medium">{conv.title}</div>
                  <div className="mt-1 text-sm text-muted">模式: {conv.mode}</div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card title="知识库" subtitle="你的知识库">
          {kbs.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-sm text-muted">
              暂无知识库，点击左侧「知识库」创建第一个
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {kbs.map((kb) => (
                <div
                  key={kb.id}
                  onClick={() => router.push(`/kb/${kb.id}`)}
                  className="rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10 cursor-pointer"
                >
                  <div className="font-medium">{kb.name}</div>
                  <div className="mt-1 text-sm text-muted">{kb.description || "暂无描述"}</div>
                  <div className="mt-2 text-xs text-muted">可见性: {kb.visibility}</div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </main>
    </Shell>
  );
}
