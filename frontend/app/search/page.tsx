"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Shell, Sidebar, Card } from "@/components/ui";
import { api, getToken, clearToken } from "@/lib/api";
import type { SearchHit } from "@/lib/api";

export default function SearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchHit[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
    } else {
      setAuthChecked(true);
    }
  }, [router]);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);
    setError(null);

    try {
      const data = await api.search(query, 10);
      setResults(data);
    } catch (err: any) {
      if (err.message?.includes("401") || err.message?.includes("403")) {
        clearToken();
        router.push("/login");
      } else {
        setError(err.message || "搜索失败");
      }
    } finally {
      setLoading(false);
    }
  }

  if (!authChecked) {
    return (
      <Shell>
        <Sidebar />
        <main className="flex-1">
          <Card title="加载中...">
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
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
        <Card title="检索" subtitle="向量检索、BM25、混合检索与重排结果">
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-3">
              <input
                className="flex-1 rounded-xl border border-white/10 bg-white/5 px-4 py-3 outline-none transition focus:border-accent/50"
                placeholder="搜索关键词"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="rounded-xl bg-accent px-6 py-3 font-medium text-slate-950 transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? "搜索中..." : "搜索"}
              </button>
            </div>
            {error && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}
          </form>
        </Card>

        {loading && (
          <Card title="搜索中...">
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
              <span className="ml-3 text-muted">正在检索相关内容...</span>
            </div>
          </Card>
        )}

        {searched && !loading && (
          <Card title={`搜索结果 (${results.length})`} subtitle={`关键词: ${query}`}>
            {error ? (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-6 text-sm text-red-400">
                搜索失败: {error}
              </div>
            ) : results.length === 0 ? (
              <div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-sm text-muted text-center">
                没有找到相关结果
              </div>
            ) : (
              <div className="space-y-3">
                {results.map((hit, index) => (
                  <div
                    key={`${hit.chunk_id}-${index}`}
                    className="rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium truncate">{hit.document_name}</span>
                      <span className="text-xs text-muted shrink-0 ml-2">
                        相似度: {(hit.similarity_score * 100).toFixed(1)}%
                      </span>
                    </div>
                    <p className="text-sm text-text line-clamp-3">{hit.content}</p>
                    <div className="mt-2 flex items-center gap-4 text-xs text-muted">
                      <span>来源类型: {hit.source_type}</span>
                      {hit.page_start && <span>页码: {hit.page_start}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        )}
      </main>
    </Shell>
  );
}
