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
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [docChunks, setDocChunks] = useState<DocumentChunk[]>([]);
  const [docPreview, setDocPreview] = useState<string>("");
  const [docTotalChunks, setDocTotalChunks] = useState(0);
  const [docLoading, setDocLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"preview" | "chunks">("preview");
  const [reprocessing, setReprocessing] = useState(false);
  const [isRenaming, setIsRenaming] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [saving, setSaving] = useState(false);

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

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    if (!uploading) {
      setIsDragging(true);
    }
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    if (uploading) return;

    const files = e.dataTransfer.files;
    if (files && files.length > 0) {
      handleUpload(files);
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

  async function handleReprocess() {
    if (!selectedDoc || reprocessing) return;
    if (!confirm(`确定要重新解析「${selectedDoc.file_name}」吗？\n向量数据会重新生成。`)) return;

    setReprocessing(true);
    setError(null);
    try {
      await api.reprocessDocument(selectedDoc.id);
      await loadData();
      await openDocDetail({ ...selectedDoc } as Document);
    } catch (err: any) {
      setError(err.message || "重新解析失败");
    } finally {
      setReprocessing(false);
    }
  }

  async function handleReprocessDoc(doc: Document) {
    if (reprocessing) return;
    if (!confirm(`确定要重新解析「${doc.file_name}」吗？\n向量数据会重新生成。`)) return;

    setReprocessing(true);
    setError(null);
    try {
      await api.reprocessDocument(doc.id);
      await loadData();
    } catch (err: any) {
      setError(err.message || "重新解析失败");
    } finally {
      setReprocessing(false);
    }
  }

  async function handleDeleteDoc(doc: Document) {
    if (!confirm(`确定要删除「${doc.file_name}」吗？\n此操作不可恢复。`)) return;

    setError(null);
    try {
      await api.deleteDocument(doc.id);
      if (selectedDoc?.id === doc.id) {
        setSelectedDoc(null);
      }
      await loadData();
    } catch (err: any) {
      setError(err.message || "删除失败");
    }
  }

  async function handleDeleteSelected() {
    if (!selectedDoc) return;
    await handleDeleteDoc(selectedDoc);
  }

  function startRename() {
    if (!selectedDoc) return;
    setRenameValue(selectedDoc.file_name);
    setIsRenaming(true);
  }

  async function handleRename() {
    if (!selectedDoc || !renameValue.trim()) return;
    try {
      const updated = await api.renameDocument(selectedDoc.id, renameValue.trim());
      setSelectedDoc(updated);
      await loadData();
    } catch (err: any) {
      setError(err.message || "重命名失败");
    } finally {
      setIsRenaming(false);
    }
  }

  function startEdit() {
    if (!docPreview) return;
    setEditContent(docPreview);
    setIsEditing(true);
  }

  async function handleSaveContent() {
    if (!selectedDoc) return;
    setSaving(true);
    setError(null);
    try {
      await api.updateDocumentContent(selectedDoc.id, editContent);
      setIsEditing(false);
      await openDocDetail({ ...selectedDoc } as Document);
      await loadData();
    } catch (err: any) {
      setError(err.message || "保存失败");
    } finally {
      setSaving(false);
    }
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

        <Card title="上传文档" subtitle="支持 .txt, .md, .pdf, .html 等格式">
          <div className="space-y-4">
            <div
              className={`rounded-xl border-2 border-dashed p-8 text-center transition cursor-pointer ${
                uploading
                  ? "border-accent/30 bg-accent/5"
                  : isDragging
                  ? "border-accent bg-accent/10 scale-[1.02]"
                  : "border-white/15 bg-white/5 hover:border-accent/50 hover:bg-white/10"
              }`}
              onClick={() => !uploading && fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.markdown,.html,.htm,.pdf"
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
                    支持 .txt, .md, .markdown, .pdf, .html, .htm 格式
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
                  className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10 hover:border-white/20"
                >
                  <div
                    className="flex items-center gap-3 flex-1 min-w-0 cursor-pointer"
                    onClick={() => openDocDetail(doc)}
                  >
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
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded-md border ${getStatusBgColor(doc.parse_status)} ${getStatusColor(doc.parse_status)}`}>
                      {getStatusText(doc.parse_status)}
                    </span>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleReprocessDoc(doc); }}
                      className="text-xs px-2 py-1 rounded-md border border-white/10 text-muted hover:text-text hover:border-white/30 transition"
                      title="重新解析"
                    >
                      🔄
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteDoc(doc); }}
                      className="text-xs px-2 py-1 rounded-md border border-red-500/20 text-red-400 hover:bg-red-500/10 hover:border-red-500/40 transition"
                      title="删除"
                    >
                      🗑️
                    </button>
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
                  <div className="min-w-0 flex-1">
                    {isRenaming ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && handleRename()}
                          className="flex-1 px-3 py-1.5 text-sm rounded-lg bg-white/5 border border-white/20 text-text focus:outline-none focus:border-accent"
                          autoFocus
                        />
                        <button
                          onClick={handleRename}
                          className="px-3 py-1.5 text-xs rounded-lg bg-accent text-white hover:bg-accent/80 transition"
                        >
                          保存
                        </button>
                        <button
                          onClick={() => setIsRenaming(false)}
                          className="px-3 py-1.5 text-xs rounded-lg border border-white/20 text-muted hover:text-text transition"
                        >
                          取消
                        </button>
                      </div>
                    ) : (
                      <h2
                        className="text-lg font-semibold truncate cursor-pointer hover:text-accent transition"
                        onClick={startRename}
                        title="点击重命名"
                      >
                        {selectedDoc.file_name}
                      </h2>
                    )}
                    <p className="text-xs text-muted mt-0.5 flex items-center gap-2 flex-wrap">
                      <span>{selectedDoc.mime_type}</span>
                      <span>·</span>
                      <span>{docTotalChunks} 个 Chunk</span>
                      {selectedDoc.metadata_?.page_count && (
                        <>
                          <span>·</span>
                          <span>{selectedDoc.metadata_.page_count} 页</span>
                        </>
                      )}
                      {selectedDoc.metadata_?.char_count && (
                        <>
                          <span>·</span>
                          <span>{selectedDoc.metadata_.char_count.toLocaleString()} 字符</span>
                        </>
                      )}
                      {selectedDoc.metadata_?.size && (
                        <>
                          <span>·</span>
                          <span>{formatFileSize(selectedDoc.metadata_.size)}</span>
                        </>
                      )}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleReprocess}
                    disabled={reprocessing}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border border-accent/30 text-accent hover:bg-accent/10 transition disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {reprocessing ? (
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
                    ) : (
                      <span>🔄</span>
                    )}
                    重新解析
                  </button>
                  <button
                    onClick={handleDeleteSelected}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-lg border border-red-500/30 text-red-400 hover:bg-red-500/10 transition"
                  >
                    🗑️ 删除
                  </button>
                  <button
                    onClick={closeDocDetail}
                    className="rounded-lg p-2 text-muted transition hover:bg-white/10 hover:text-text"
                  >
                    ✕
                  </button>
                </div>
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
                    {isEditing ? (
                      <div className="space-y-3">
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="w-full h-96 px-4 py-3 text-sm rounded-xl bg-white/5 border border-white/20 text-text focus:outline-none focus:border-accent font-mono leading-relaxed resize-y"
                          placeholder="编辑文档内容..."
                        />
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted">
                            {editContent.length} 字符
                          </span>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setIsEditing(false)}
                              disabled={saving}
                              className="px-4 py-2 text-sm rounded-lg border border-white/20 text-muted hover:text-text transition disabled:opacity-50"
                            >
                              取消
                            </button>
                            <button
                              onClick={handleSaveContent}
                              disabled={saving}
                              className="px-4 py-2 text-sm rounded-lg bg-accent text-white hover:bg-accent/80 transition disabled:opacity-50 flex items-center gap-2"
                            >
                              {saving && (
                                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
                              )}
                              保存
                            </button>
                          </div>
                        </div>
                      </div>
                    ) : docPreview ? (
                      <>
                        <div className="flex items-center justify-between mb-3">
                          <div className="text-xs text-muted">
                            文档预览（前 5 个 Chunk）
                          </div>
                          {selectedDoc && ["txt", "md", "markdown", "html", "htm"].includes(selectedDoc.file_type) && (
                            <button
                              onClick={startEdit}
                              className="text-xs px-3 py-1 rounded-md border border-accent/30 text-accent hover:bg-accent/10 transition"
                            >
                              ✏️ 编辑内容
                            </button>
                          )}
                        </div>
                        <div className="whitespace-pre-wrap text-sm leading-relaxed text-text/90 bg-white/5 rounded-xl p-4 border border-white/10">
                          {docPreview}
                          {docTotalChunks > 5 && (
                            <div className="mt-4 pt-3 border-t border-white/10 text-xs text-muted">
                              仅展示前 5 个 Chunk 的内容，完整内容请查看 Chunk 列表
                            </div>
                          )}
                        </div>
                      </>
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
