"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell, Sidebar, Card } from "@/components/ui";
import { api, getToken, clearToken } from "@/lib/api";
import type { KnowledgeBase } from "@/lib/api";

export default function KnowledgeBasesPage() {
  const router = useRouter();
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newVisibility, setNewVisibility] = useState("private");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadKbs();
  }, [router]);

  async function loadKbs() {
    try {
      const data = await api.listKnowledgeBases();
      setKbs(data);
    } catch (err) {
      clearToken();
      router.push("/login");
    } finally {
      setLoading(false);
    }
  }

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreating(true);

    try {
      await api.createKnowledgeBase(newName, newDesc || undefined, newVisibility);
      setNewName("");
      setNewDesc("");
      setShowCreate(false);
      await loadKbs();
    } catch (err: any) {
      setError(err.message || "创建失败");
    } finally {
      setCreating(false);
    }
  }

  async function handleDelete(id: string) {
    if (!confirm("确定要删除这个知识库吗？")) return;
    try {
      await api.deleteKnowledgeBase(id);
      await loadKbs();
    } catch (err: any) {
      alert("删除失败: " + err.message);
    }
  }

  if (loading) {
    return (
      <Shell>
        <Sidebar />
        <main className="flex-1">
          <Card title="加载中...">
            <div className="text-muted text-sm">正在加载数据...</div>
          </Card>
        </main>
      </Shell>
    );
  }

  return (
    <Shell>
      <Sidebar />
      <main className="flex-1 space-y-6">
        <Card title="知识库管理" subtitle="创建、编辑、删除和成员管理">
          <div className="mb-4 flex justify-between items-center">
            <p className="text-sm text-muted">共 {kbs.length} 个知识库</p>
            <button
              onClick={() => setShowCreate(!showCreate)}
              className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-slate-950 transition hover:opacity-90"
            >
              {showCreate ? "取消" : "+ 新建知识库"}
            </button>
          </div>

          {showCreate && (
            <form onSubmit={handleCreate} className="mb-6 grid gap-3 rounded-xl border border-white/10 bg-white/5 p-4">
              <input
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 outline-none"
                placeholder="知识库名称"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                required
              />
              <input
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 outline-none"
                placeholder="描述（可选）"
                value={newDesc}
                onChange={(e) => setNewDesc(e.target.value)}
              />
              <select
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 outline-none"
                value={newVisibility}
                onChange={(e) => setNewVisibility(e.target.value)}
              >
                <option value="private">私有</option>
                <option value="public">公开</option>
              </select>
              {error && (
                <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-2 text-sm text-red-400">
                  {error}
                </div>
              )}
              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={creating}
                  className="rounded-xl bg-accent px-4 py-2 text-sm font-medium text-slate-950 transition hover:opacity-90 disabled:opacity-50"
                >
                  {creating ? "创建中..." : "创建"}
                </button>
              </div>
            </form>
          )}

          {kbs.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-sm text-muted">
              暂无知识库，点击右上角「新建知识库」开始
            </div>
          ) : (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {kbs.map((kb) => (
                <div
                  key={kb.id}
                  onClick={() => router.push(`/kb/${kb.id}`)}
                  className="group rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10 cursor-pointer"
                >
                  <div className="font-medium">{kb.name}</div>
                  <div className="mt-1 text-sm text-muted">{kb.description || "暂无描述"}</div>
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-muted">{kb.visibility}</span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(kb.id);
                      }}
                      className="text-xs text-red-400 opacity-0 transition group-hover:opacity-100 hover:text-red-300"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </main>
    </Shell>
  );
}
