"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Card, Shell, Sidebar } from "@/components/ui";
import { api, clearToken, getToken } from "@/lib/api";
import type { Document, DocumentChunk, KnowledgeBase } from "@/lib/api";

const EDITABLE_FILE_TYPES = new Set(["txt", "md", "markdown", "html", "htm"]);

function getStatusColor(status: string) {
  switch (status) {
    case "completed":
      return "text-green-400";
    case "processing":
      return "text-yellow-400";
    case "pending":
      return "text-sky-400";
    case "empty":
      return "text-slate-300";
    case "failed":
      return "text-red-400";
    default:
      return "text-muted";
  }
}

function getStatusBgColor(status: string) {
  switch (status) {
    case "completed":
      return "border-green-500/30 bg-green-500/10";
    case "processing":
      return "border-yellow-500/30 bg-yellow-500/10";
    case "pending":
      return "border-sky-500/30 bg-sky-500/10";
    case "empty":
      return "border-slate-500/30 bg-slate-500/10";
    case "failed":
      return "border-red-500/30 bg-red-500/10";
    default:
      return "border-white/10 bg-white/5";
  }
}

function getStatusText(status: string) {
  switch (status) {
    case "pending":
      return "排队中";
    case "processing":
      return "处理中";
    case "completed":
      return "已完成";
    case "empty":
      return "无可用内容";
    case "failed":
      return "处理失败";
    default:
      return status;
  }
}

function getStatusHint(status: string) {
  switch (status) {
    case "pending":
      return "文档已进入处理队列，请稍后刷新查看结果。";
    case "processing":
      return "系统正在解析文档并生成分段。";
    case "completed":
      return "文档解析完成，可以预览内容和分段。";
    case "empty":
      return "文档已完成解析，但没有提取到可用于检索的内容。";
    case "failed":
      return "文档处理失败，建议重新解析或重新上传。";
    default:
      return "当前状态暂未定义。";
  }
}

function formatFileSize(bytes: string | number) {
  const size = typeof bytes === "string" ? parseInt(bytes, 10) : bytes;
  if (Number.isNaN(size)) return "未知";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

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
  const [docPreview, setDocPreview] = useState("");
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
      if (selectedDoc) {
        const refreshed = docsResp.find((doc) => doc.id === selectedDoc.id);
        if (refreshed) {
          setSelectedDoc(refreshed);
        }
      }
    } catch {
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
      await api.uploadDocument(kbId, files[0]);
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
    if (!uploading) setIsDragging(true);
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
    setIsEditing(false);
    setIsRenaming(false);

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
    setIsEditing(false);
    setIsRenaming(false);
  }

  async function handleReprocess() {
    if (!selectedDoc || reprocessing) return;
    if (!confirm(`确定要重新解析「${selectedDoc.file_name}」吗？\n系统会重新生成向量和全文索引。`)) return;

    setReprocessing(true);
    setError(null);
    try {
      await api.reprocessDocument(selectedDoc.id);
      await loadData();
      await openDocDetail({ ...selectedDoc });
    } catch (err: any) {
      setError(err.message || "重新解析失败");
    } finally {
      setReprocessing(false);
    }
  }

  async function handleReprocessDoc(doc: Document) {
    if (reprocessing) return;
    if (!confirm(`确定要重新解析「${doc.file_name}」吗？\n系统会重新生成向量和全文索引。`)) return;

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
    if (!confirm(`确定要删除「${doc.file_name}」吗？\n该操作不可恢复。`)) return;

    setError(null);
    try {
      await api.deleteDocument(doc.id);
      if (selectedDoc?.id === doc.id) {
        closeDocDetail();
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
      await openDocDetail({ ...selectedDoc });
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
          <Card title="加载中">
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
              <span className="ml-3 text-muted">正在加载知识库数据...</span>
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
              className="text-sm text-muted transition hover:text-text"
            >
              ← 返回知识库列表
            </button>
            <h1 className="mt-2 text-2xl font-semibold">{kb?.name}</h1>
            <p className="mt-1 text-sm text-muted">{kb?.description || "暂无描述"}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted">可见性：{kb?.visibility}</span>
          </div>
        </div>

        <Card title="上传文档" subtitle="支持 .txt、.md、.pdf、.html 等常见文本格式">
          <div className="space-y-4">
            <div
              className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition ${
                uploading
                  ? "border-accent/30 bg-accent/5"
                  : isDragging
                    ? "scale-[1.02] border-accent bg-accent/10"
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
                  <span className="text-muted">正在上传并处理，请稍候...</span>
                </div>
              ) : (
                <>
                  <div className="text-lg font-medium">点击或拖拽文件到这里上传</div>
                  <div className="mt-2 text-sm text-muted">
                    支持 .txt、.md、.markdown、.pdf、.html、.htm
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

        <Card title={`文档列表（${documents.length}）`} subtitle="点击文档可查看预览、状态与分段详情">
          {documents.length === 0 ? (
            <div className="rounded-xl border border-dashed border-white/15 bg-white/5 p-6 text-center text-sm text-muted">
              暂无文档，先上传第一份资料吧。
            </div>
          ) : (
            <div className="space-y-2">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-xl border border-white/10 bg-white/5 p-4 transition hover:border-white/20 hover:bg-white/10"
                >
                  <div
                    className="flex min-w-0 flex-1 cursor-pointer items-center gap-3"
                    onClick={() => openDocDetail(doc)}
                  >
                    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-accent">
                      文
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate font-medium">{doc.file_name}</div>
                      <div className="mt-1 flex items-center gap-2 text-xs text-muted">
                        <span>{doc.mime_type}</span>
                        <span>·</span>
                        <span className={getStatusColor(doc.parse_status)}>
                          {getStatusText(doc.parse_status)}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`rounded-md border px-2 py-1 text-xs ${getStatusBgColor(doc.parse_status)} ${getStatusColor(doc.parse_status)}`}
                    >
                      {getStatusText(doc.parse_status)}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleReprocessDoc(doc);
                      }}
                      className="rounded-md border border-white/10 px-2 py-1 text-xs text-muted transition hover:border-white/30 hover:text-text"
                      title="重新解析"
                    >
                      重试
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteDoc(doc);
                      }}
                      className="rounded-md border border-red-500/20 px-2 py-1 text-xs text-red-400 transition hover:border-red-500/40 hover:bg-red-500/10"
                      title="删除文档"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        {selectedDoc && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm">
            <div className="flex max-h-[85vh] w-full max-w-4xl flex-col rounded-2xl border border-white/10 bg-panel shadow-xl">
              <div className="flex items-center justify-between border-b border-white/10 p-5">
                <div className="flex min-w-0 items-center gap-3">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-accent/20 text-accent">
                    文
                  </div>
                  <div className="min-w-0 flex-1">
                    {isRenaming ? (
                      <div className="flex items-center gap-2">
                        <input
                          type="text"
                          value={renameValue}
                          onChange={(e) => setRenameValue(e.target.value)}
                          onKeyDown={(e) => e.key === "Enter" && handleRename()}
                          className="flex-1 rounded-lg border border-white/20 bg-white/5 px-3 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
                          autoFocus
                        />
                        <button
                          onClick={handleRename}
                          className="rounded-lg bg-accent px-3 py-1.5 text-xs text-white transition hover:bg-accent/80"
                        >
                          保存
                        </button>
                        <button
                          onClick={() => setIsRenaming(false)}
                          className="rounded-lg border border-white/20 px-3 py-1.5 text-xs text-muted transition hover:text-text"
                        >
                          取消
                        </button>
                      </div>
                    ) : (
                      <h2
                        className="cursor-pointer truncate text-lg font-semibold transition hover:text-accent"
                        onClick={startRename}
                        title="点击重命名"
                      >
                        {selectedDoc.file_name}
                      </h2>
                    )}
                    <p className="mt-0.5 flex flex-wrap items-center gap-2 text-xs text-muted">
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
                    className="flex items-center gap-1.5 rounded-lg border border-accent/30 px-3 py-1.5 text-xs text-accent transition hover:bg-accent/10 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {reprocessing && (
                      <div className="h-3 w-3 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
                    )}
                    重新解析
                  </button>
                  <button
                    onClick={handleDeleteSelected}
                    className="flex items-center gap-1.5 rounded-lg border border-red-500/30 px-3 py-1.5 text-xs text-red-400 transition hover:bg-red-500/10"
                  >
                    删除
                  </button>
                  <button
                    onClick={closeDocDetail}
                    className="rounded-lg p-2 text-muted transition hover:bg-white/10 hover:text-text"
                    title="关闭"
                  >
                    ×
                  </button>
                </div>
              </div>

              <div className="border-b border-white/10 px-5 py-3">
                <div className="flex flex-wrap items-center gap-3">
                  <span
                    className={`rounded-md border px-2 py-1 text-xs ${getStatusBgColor(selectedDoc.parse_status)} ${getStatusColor(selectedDoc.parse_status)}`}
                  >
                    {getStatusText(selectedDoc.parse_status)}
                  </span>
                  <span className="text-xs text-muted">{getStatusHint(selectedDoc.parse_status)}</span>
                </div>
              </div>

              <div className="flex border-b border-white/10">
                <button
                  onClick={() => setActiveTab("preview")}
                  className={`border-b-2 px-5 py-3 text-sm font-medium transition ${
                    activeTab === "preview"
                      ? "border-accent text-text"
                      : "border-transparent text-muted hover:text-text"
                  }`}
                >
                  文档预览
                </button>
                <button
                  onClick={() => setActiveTab("chunks")}
                  className={`border-b-2 px-5 py-3 text-sm font-medium transition ${
                    activeTab === "chunks"
                      ? "border-accent text-text"
                      : "border-transparent text-muted hover:text-text"
                  }`}
                >
                  Chunk 列表（{docChunks.length}）
                </button>
              </div>

              <div className="flex-1 overflow-auto p-5">
                {docLoading ? (
                  <div className="flex items-center justify-center py-12">
                    <div className="h-8 w-8 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
                    <span className="ml-3 text-muted">正在加载文档内容...</span>
                  </div>
                ) : activeTab === "preview" ? (
                  <div className="prose prose-invert max-w-none">
                    {isEditing ? (
                      <div className="space-y-3">
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="h-96 w-full resize-y rounded-xl border border-white/20 bg-white/5 px-4 py-3 font-mono text-sm leading-relaxed text-text focus:border-accent focus:outline-none"
                          placeholder="编辑文档正文..."
                        />
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-muted">{editContent.length} 字符</span>
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => setIsEditing(false)}
                              disabled={saving}
                              className="rounded-lg border border-white/20 px-4 py-2 text-sm text-muted transition hover:text-text disabled:opacity-50"
                            >
                              取消
                            </button>
                            <button
                              onClick={handleSaveContent}
                              disabled={saving}
                              className="flex items-center gap-2 rounded-lg bg-accent px-4 py-2 text-sm text-white transition hover:bg-accent/80 disabled:opacity-50"
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
                        <div className="mb-3 flex items-center justify-between">
                          <div className="text-xs text-muted">当前仅展示前 5 个 Chunk 的预览内容。</div>
                          {selectedDoc && EDITABLE_FILE_TYPES.has(selectedDoc.file_type) && (
                            <button
                              onClick={startEdit}
                              className="rounded-md border border-accent/30 px-3 py-1 text-xs text-accent transition hover:bg-accent/10"
                            >
                              编辑正文
                            </button>
                          )}
                        </div>
                        <div className="whitespace-pre-wrap rounded-xl border border-white/10 bg-white/5 p-4 text-sm leading-relaxed text-text/90">
                          {docPreview}
                          {docTotalChunks > 5 && (
                            <div className="mt-4 border-t border-white/10 pt-3 text-xs text-muted">
                              这里只展示前 5 个 Chunk。若需完整检查，请切换到 Chunk 列表。
                            </div>
                          )}
                        </div>
                      </>
                    ) : (
                      <div className="py-8 text-center text-muted">
                        {selectedDoc.parse_status === "pending" || selectedDoc.parse_status === "processing"
                          ? "文档仍在处理中，暂时还没有可预览内容。"
                          : "暂无预览内容。"}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-3">
                    {docChunks.length === 0 ? (
                      <div className="py-8 text-center text-muted">
                        {selectedDoc.parse_status === "completed" || selectedDoc.parse_status === "empty"
                          ? "当前文档还没有 Chunk 数据。"
                          : "文档处理完成后，这里会展示 Chunk 列表。"}
                      </div>
                    ) : (
                      docChunks.map((chunk, index) => (
                        <div
                          key={chunk.id}
                          className="rounded-xl border border-white/10 bg-white/5 p-4 transition hover:bg-white/10"
                        >
                          <div className="mb-2 flex items-center justify-between">
                            <span className="text-xs font-medium text-accent">
                              Chunk #{chunk.chunk_no || index + 1}
                            </span>
                            <span className="text-xs text-muted">{chunk.content.length} 字符</span>
                          </div>
                          <div className="whitespace-pre-wrap text-sm leading-relaxed text-text/90">
                            {chunk.content}
                          </div>
                          {chunk.page_start !== null && chunk.page_end !== null && (
                            <div className="mt-2 text-xs text-muted">
                              页码：{chunk.page_start} - {chunk.page_end}
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
