"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter, useParams } from "next/navigation";
import { Shell, Sidebar, Card } from "@/components/ui";
import { api, getToken, clearToken } from "@/lib/api";
import type { KnowledgeBase, Document, DocumentChunk } from "@/lib/api";

export default function KnowledgeBaseDetailPage() {
  const router = useRouter();
  const params = useParams();
  const kbId = params.id as string;
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [kb, setKb] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [docChunks, setDocChunks] = useState<DocumentChunk[]>([]);
  const [docPreview, setDocPreview] = useState<string>("");
  const [docTotalChunks, setDocTotalChunks] = useState(0);
  const [docLoading, setDocLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"preview" | "chunks">("preview");

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    if (kbId) {
      loadData();
    }
  }, [router, kbId]);

  async function loadData() {
    try {
      const [kbResp, docsResp] = await Promise.all([
        api.getKnowledgeBase(kbId),
        api.listDocuments(kbId),
      ]);
      setKb(kbResp);
      setDocuments(docsResp);
    } catch (err) {
      clearToken();
      router.push("/login");
    } finally {
      setLoading(false);
    }
  }

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) return;

    setError(null);
    setUploading(true);

    try {
      const file = files[0];
      await api.uploadDocument(kbId, file);
      await loadData();
    } catch (err: any) {
      setError(err.message || "上传失败");
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }

  async function openDocDetail(doc: Document) {
    setSelectedDoc(doc);
    setDocLoading(true);
    setActiveTab("preview");
    try {
      const [previewResp, chunksResp] = await Promise.all([
        api.getDocumentPreview(doc.id),
        api.listDocumentChunks(doc.id),
      ]);
      setDocPreview(previewResp.preview);
      setDocTotalChunks(previewResp.total_chunks);
      setDocChunks(chunksResp);
    } catch (err: any) {
      setError(err.message || "加载文档详情失败");
    } finally {
      setDocLoading(false);
    }
  }

  function closeDocDetail() {
    setSelectedDoc(null);
    setDocChunks([]);
    setDocPreview("");
    setDocTotalChunks(0);
  }

  function getStatusColor(status: string) {
    switch (status) {
      case "completed":
        return "text-green-400";
      case "processing":
        return "text-yellow-400";
      case "failed":
        return "text-red-400";
      default:
        return "text-muted";
    }
  }

  function getStatusBgColor(status: string) {
    switch (status) {
      case "completed":
        return "bg-green-500/10 border-green-500/30";
      case "processing":
        return "bg-yellow-500/10 border-yellow-500/30";
      case "failed":
        return "bg-red-500/10 border-red-500/30";
      default:
        return "bg-white/5 border-white/10";
    }
  }

  function getStatusText(status: string) {
    switch (status) {
      case "completed":
        return "已完成";
      case "processing":
        return "处理中";
      case "failed":
        return "失败";
      default:
        return status;
    }
  }

  function formatFileSize(bytes: string | number) {
    const size = typeof bytes === "string" ? parseInt(bytes) : bytes;
    if (isNaN(size)) return "未知";
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

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
        <div className="flex items-center justify-between">
          <div>
            <button
              onClick={() => router.push("/kb")}
              className="text-sm text-muted hover:text-text transition"
            >
              ← 返回知识库列表
            </button>
            <h1 className="mt-2 text-2xl font-semibold">{kb?.name}</h1>
            <p className="mt-1 text-sm text-muted">{kb?.description || "暂无描述"}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted">可见性: {kb?.visibility}</span>
          </div>
        </div>

        <Card title="上传文档" subtitle="支持 .txt, .md, .html 等文本格式">
          <div className="space-y-4">
            <div
              className={`rounded-xl border-2 border-dashed p-8 text-center transition cursor-pointer ${
                uploading
                  ? "border-accent/30 bg-accent/5"
                  : "border-white/15 bg-white/5 hover:border-accent/50 hover:bg-white/10"
              }`}
              onClick={() => !uploading && fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.markdown,.html,.htm"
                onChange={(e) => handleUpload(e.target.files)}
                disabled={uploading}
                className="hidden"
              />
              {uploading ? (
                <div className="flex items-center justify-center gap-3">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
                  <span className="text-muted">上传处理中，请稍候...</span>
                </div>
              ) : (
                <>
                  <div className="text-lg font-medium">点击或拖拽上传文件</div>
                  <div className="mt-2 text-sm text-muted">
                    支持 .txt, .md, .markdown, .html, .htm 格式
                  </div>
                </>
              )}
            </div>

            {error && (
              <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
                {error}
              </div>
            )}
          </div>
        </Card>

        <Card title={`文档列表 (${documents.length})`} subtitle="点击文档可查看详情和 Chunk 列表">
          {documents.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-sm text-muted text-center">
              暂无文档，上传第一个文档开始吧
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => openDocDetail(doc)}
                  className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10 hover:border-white/20 cursor-pointer"
                >
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-accent">
                      📄
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="font-medium truncate">{doc.file_name}</div>
                      <div className="mt-1 text-xs text-muted flex items-center gap-2">
                        <span>{doc.mime_type}</span>
                        <span>·</span>
                        <span className={getStatusColor(doc.parse_status)}>
                          {getStatusText(doc.parse_status)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2 py-1 rounded-md border ${getStatusBgColor(doc.parse_status)} ${getStatusColor(doc.parse_status)}`}>
                      {getStatusText(doc.parse_status)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {selectedDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-4xl max-h-[85vh] rounded-2xl border border-white/10 bg-panel shadow-xl flex flex-col">
              <div className="flex items-center justify-between p-5 border-b border-white/10">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-accent">
                    📄
                  </div>
                  <div className="min-w-0">
                    <h2 className="text-lg font-semibold truncate">{selectedDoc.file_name}</h2>
                    <p className="text-xs text-muted mt-0.5">
                      {selectedDoc.mime_type} · {docTotalChunks} 个 Chunk
                    </p>
                  </div>
                </div>
                <button
                  onClick={closeDocDetail}
                  className="rounded-lg p-2 text-muted transition hover:bg-white/10 hover:text-text"
                >
                  ✕
                </button>
              </div>

              <div className="flex border-b border-white/10">
                <button
                  onClick={() => setActiveTab("preview")}
                  className={`px-5 py-3 text-sm font-medium transition border-b-2 ${
                    activeTab === "preview"
                      ? "border-accent text-text"
                      : "border-transparent text-muted hover:text-text"
                  }`}
                >
                  文档预览
                </button>
                <button
                  onClick={() => setActiveTab("chunks")}
                  className={`px-5 py-3 text-sm font-medium transition border-b-2 ${
                    activeTab === "chunks"
                      ? "border-accent text-text"
                      : "border-transparent text-muted hover:text-text"
                  }`}
                >
                  Chunk 列表 ({docChunks.length})
                </button>
              </div>

              <div className="flex-1 overflow-auto p-5">
                {docLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
                    <span className="ml-3 text-muted">加载中...</span>
                  </div>
                ) : activeTab === "preview" ? (
                  <div className="prose prose-invert max-w-none">
                    {docPreview ? (
                      <div className="whitespace-pre-wrap text-sm leading-relaxed text-text/90 bg-white/5 rounded-xl p-4 border border-white/10">
                        {docPreview}
                        {docTotalChunks > 5 && (
                          <div className="mt-4 pt-3 border-t border-white/10 text-xs text-muted">
                            仅展示前 5 个 Chunk 的内容，完整内容请查看 Chunk 列表
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted">
                        暂无预览内容
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {docChunks.length === 0 ? (
                      <div className="text-center py-8 text-muted">
                        暂无 Chunk 数据
                      </div>
                    ) : (
                      docChunks.map((chunk, index) => (
                        <div
                          key={chunk.id}
                          className="rounded-xl border border-white/10 bg-white/5 p-4 hover:bg-white/10 transition"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs font-medium text-accent">
                              Chunk #{chunk.chunk_no || index + 1}
                            </span>
                            <span className="text-xs text-muted">
                              {chunk.content.length} 字符
                            </span>
                          </div>
                          <div className="text-sm text-text/90 whitespace-pre-wrap leading-relaxed">
                            {chunk.content}
                          </div>
                          {chunk.page_start !== null && chunk.page_end !== null && (
                            <div className="mt-2 text-xs text-muted">
                              页码: {chunk.page_start} - {chunk.page_end}
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </main>
    </Shell>
  );
}
