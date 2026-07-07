"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Shell, Sidebar, Badge } from "@/components/ui";
import { api, clearToken, getToken } from "@/lib/api";
import type { Conversation, KnowledgeBase, Message } from "@/lib/api";
import { Bot, Check, ChevronDown, Copy, MessageSquare, Plus, Send, Sparkles, Trash2, User } from "lucide-react";
import MarkdownMessage from "@/components/MarkdownMessage";

export default function ChatPage() {
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConv, setCurrentConv] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
  const [selectedKb, setSelectedKb] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedCitations, setExpandedCitations] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadInitialData();
  }, [router]);

  const filteredConversations = selectedKb
    ? conversations.filter((c) => c.kb_id === selectedKb)
    : conversations;

  useEffect(() => {
    if (currentConv && currentConv.kb_id !== selectedKb) {
      if (filteredConversations.length > 0) {
        handleSelectConversation(filteredConversations[0]);
      } else {
        setCurrentConv(null);
        setMessages([]);
      }
    }
  }, [selectedKb, conversations]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadInitialData() {
    try {
      setError(null);
      const [convsResp, kbsResp] = await Promise.all([
        api.listConversations(),
        api.listKnowledgeBases(),
      ]);
      setConversations(convsResp);
      setKbs(kbsResp);

      if (kbsResp.length > 0) {
        setSelectedKb(kbsResp[0].id);
        const kbConvs = convsResp.filter((c) => c.kb_id === kbsResp[0].id);
        if (kbConvs.length > 0) {
          setCurrentConv(kbConvs[0]);
          setLoadingMessages(true);
          try {
            const msgs = await api.listMessages(kbConvs[0].id);
            setMessages(msgs);
          } finally {
            setLoadingMessages(false);
          }
        }
      }
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

  async function handleSelectConversation(conv: Conversation) {
    setCurrentConv(conv);
    setLoadingMessages(true);
    setError(null);
    try {
      const msgs = await api.listMessages(conv.id);
      setMessages(msgs);
    } catch (err: any) {
      setError(err.message || "加载消息失败");
    } finally {
      setLoadingMessages(false);
    }
  }

  async function handleNewConversation() {
    if (kbs.length === 0) {
      setError("请先创建一个知识库");
      return;
    }
    setError(null);
    try {
      const conv = await api.createConversation(selectedKb || undefined, "新对话");
      setConversations([conv, ...conversations]);
      setCurrentConv(conv);
      setMessages([]);
    } catch (err: any) {
      setError(err.message || "创建对话失败");
    }
  }

  async function handleDeleteConversation(convId: string, e: React.MouseEvent) {
    e.stopPropagation();
    if (!confirm("确定要删除这个对话吗？")) return;

    try {
      await api.deleteConversation(convId);
      const newConversations = conversations.filter((c) => c.id !== convId);
      setConversations(newConversations);

      if (currentConv?.id === convId) {
        const remaining = selectedKb
          ? newConversations.filter((c) => c.kb_id === selectedKb)
          : newConversations;

        if (remaining.length > 0) {
          setCurrentConv(remaining[0]);
          setLoadingMessages(true);
          try {
            const msgs = await api.listMessages(remaining[0].id);
            setMessages(msgs);
          } finally {
            setLoadingMessages(false);
          }
        } else {
          setCurrentConv(null);
          setMessages([]);
        }
      }
    } catch (err: any) {
      setError(err.message || "删除对话失败");
    }
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending) return;

    let conv = currentConv;
    if (!conv) {
      if (kbs.length === 0) {
        setError("请先创建一个知识库");
        return;
      }
      try {
        conv = await api.createConversation(selectedKb || undefined, input.slice(0, 30));
        setConversations([conv, ...conversations]);
        setCurrentConv(conv);
      } catch (err: any) {
        setError(err.message || "创建对话失败");
        return;
      }
    }

    const userMessage: Message = {
      id: "temp-user",
      conversation_id: conv.id,
      role: "user",
      content: input,
      citations: [],
      usage: {},
    };

    const assistantMessage: Message = {
      id: "temp-assistant",
      conversation_id: conv.id,
      role: "assistant",
      content: "",
      citations: [],
      usage: {},
    };

    setMessages([...messages, userMessage, assistantMessage]);
    const userInput = input;
    setInput("");
    setSending(true);
    setError(null);

    try {
      const stream = api.sendMessageStream(conv.id, userInput);
      let fullContent = "";
      let citations: any[] = [];
      let finalUsage: Record<string, any> = {};

      for await (const event of stream) {
        if (event.type === "citations") {
          citations = event.citations || [];
          setMessages((prev) =>
            prev.map((m) => (m.id === "temp-assistant" ? { ...m, citations } : m)),
          );
        } else if (event.type === "delta") {
          fullContent += event.content;
          setMessages((prev) =>
            prev.map((m) => (m.id === "temp-assistant" ? { ...m, content: fullContent } : m)),
          );
        } else if (event.type === "done") {
          finalUsage = event.usage || {};
          setMessages((prev) =>
            prev.map((m) => (m.id === "temp-assistant" ? { ...m, usage: finalUsage } : m)),
          );
        } else if (event.type === "error") {
          throw new Error(event.message || "生成回答失败");
        }
      }

      const updatedConvs = await api.listConversations();
      setConversations(updatedConvs);
    } catch (err: any) {
      setError(err.message || "发送失败");
      setMessages((prev) => prev.filter((m) => m.id !== "temp-user" && m.id !== "temp-assistant"));
    } finally {
      setSending(false);
    }
  }

  function cleanAnswerContent(content: string): string {
    return content
      .replace(/\n*###\s*引用来源[\s\S]*$/, "")
      .replace(/\n*\*\*引用来源\*\*[\s\S]*$/, "")
      .replace(/\n*引用来源[:：][\s\S]*$/, "")
      .replace(/\n+$/g, "");
  }

  async function handleCopyAnswer(content: string) {
    const cleanContent = cleanAnswerContent(content);
    try {
      await navigator.clipboard.writeText(cleanContent);
      const msg = messages.find((m) => m.content === content);
      if (msg) {
        setCopiedId(msg.id);
        setTimeout(() => setCopiedId(null), 2000);
      }
    } catch (err) {
      console.error("Copy failed:", err);
    }
  }

  function toggleCitations(messageId: string) {
    setExpandedCitations((prev) => ({
      ...prev,
      [messageId]: !prev[messageId],
    }));
  }

  if (loading) {
    return (
      <Shell>
        <Sidebar />
        <main className="flex-1">
          <div className="rounded-2xl glass p-8 shadow-glass">
            <div className="flex items-center justify-center py-8">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
              <span className="ml-3 text-muted">正在加载数据...</span>
            </div>
          </div>
        </main>
      </Shell>
    );
  }

  return (
    <Shell>
      <Sidebar />
      <main className="flex h-[calc(100vh-3rem)] flex-1 gap-6">
        <div className="w-64 shrink-0 space-y-4">
          <div className="space-y-3">
            <div className="group relative">
              <select
                value={selectedKb}
                onChange={(e) => setSelectedKb(e.target.value)}
                className="w-full appearance-none rounded-xl border border-glass-border bg-bg-secondary/80 px-4 py-2.5 pr-10 text-sm text-text outline-none transition-all duration-300 hover:border-glass-border/80 focus:border-primary/50 focus:bg-bg-secondary"
              >
                {kbs.map((kb) => (
                  <option key={kb.id} value={kb.id} className="bg-bg-secondary text-text">
                    {kb.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted transition-transform group-hover:text-text" />
            </div>
            <button
              onClick={handleNewConversation}
              className="btn-gradient flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-medium text-white"
            >
              <Plus className="h-4 w-4" />
              新对话
            </button>
          </div>

          {error && (
            <div className="animate-fade-in rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
              {error}
            </div>
          )}

          <div className="glass rounded-2xl p-4 shadow-glass">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-primary" />
                <span className="text-xs font-medium uppercase tracking-[0.15em] text-muted">对话列表</span>
              </div>
              <span className="text-xs text-muted">{filteredConversations.length}</span>
            </div>
            <div className="scrollbar-thin max-h-[55vh] space-y-1 overflow-y-auto pr-1">
              {filteredConversations.length === 0 ? (
                <div className="py-4 text-center text-xs text-muted">当前知识库下还没有对话</div>
              ) : (
                filteredConversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`group relative rounded-xl transition-all duration-200 ${
                      currentConv?.id === conv.id
                        ? "bg-gradient-to-r from-primary/20 to-secondary/10"
                        : "hover:bg-white/5"
                    }`}
                  >
                    <button
                      onClick={() => handleSelectConversation(conv)}
                      className={`w-full px-3 py-2.5 pr-10 text-left text-sm transition-all duration-200 ${
                        currentConv?.id === conv.id ? "text-white" : "text-muted hover:text-text"
                      }`}
                    >
                      <div className="truncate font-medium">{conv.title}</div>
                    </button>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-muted opacity-0 transition-all duration-200 hover:bg-red-500/20 hover:text-red-400 group-hover:opacity-100"
                      title="删除对话"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="glass flex flex-1 flex-col overflow-hidden rounded-2xl shadow-glass">
          <div className="border-b border-glass-border/50 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="flex items-center gap-2 text-lg font-semibold">
                  <Sparkles className="h-5 w-5 text-primary" />
                  {currentConv ? currentConv.title : "知识库问答"}
                </h2>
                <p className="mt-0.5 text-sm text-muted">支持流式回答与引用来源展示。</p>
              </div>
              {selectedKb && (
                <Badge variant="primary">
                  {kbs.find((kb) => kb.id === selectedKb)?.name || "已选知识库"}
                </Badge>
              )}
            </div>
          </div>

          <div className="scrollbar-thin flex-1 space-y-6 overflow-y-auto p-6">
            {loadingMessages ? (
              <div className="flex h-full items-center justify-center">
                <div className="flex items-center gap-3 text-muted">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
                  <span>正在加载消息...</span>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="flex h-full items-center justify-center text-muted">
                <div className="text-center">
                  <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-primary/20 to-secondary/10">
                    <Sparkles className="h-8 w-8 text-primary" />
                  </div>
                  <p className="text-lg font-semibold text-text">开始新的对话</p>
                  <p className="mt-2 max-w-sm text-sm text-muted">
                    选择知识库后，在下方输入问题，即可开始问答。
                  </p>
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={msg.id}
                  className={`animate-fade-in-up flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {msg.role === "assistant" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[75%] rounded-2xl px-5 py-4 ${
                      msg.role === "user"
                        ? "bg-gradient-to-br from-primary to-secondary text-white shadow-lg shadow-primary/20"
                        : "glass text-text shadow-sm"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <MarkdownMessage content={cleanAnswerContent(msg.content)} />
                    ) : (
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</p>
                    )}

                    {msg.citations && msg.citations.length > 0 && (() => {
                      const seen = new Set<string>();
                      const unique = msg.citations.filter((cit: any) => {
                        const key = `${cit.document_name || "未知文档"}-${cit.page_start || ""}-${cit.page_end || ""}`;
                        if (seen.has(key)) return false;
                        seen.add(key);
                        return true;
                      });

                      const citations = unique.slice(0, 5);
                      const isExpanded = expandedCitations[msg.id] ?? false;

                      return (
                        <div className="mt-4 border-t border-glass-border pt-3">
                          <button
                            type="button"
                            onClick={() => toggleCitations(msg.id)}
                            className="flex w-full items-center justify-between rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-left transition hover:border-white/20 hover:bg-white/10"
                          >
                            <div className="min-w-0">
                              <p className="text-xs font-medium text-muted">引用来源</p>
                              <p className="mt-1 truncate text-[11px] text-muted/80">
                                {citations.length} 条来源，{isExpanded ? "点击收起" : "点击展开查看详情"}
                              </p>
                            </div>
                            <ChevronDown
                              className={`h-4 w-4 shrink-0 text-muted transition-transform ${
                                isExpanded ? "rotate-180" : ""
                              }`}
                            />
                          </button>

                          {isExpanded && (
                            <ul className="mt-3 space-y-1.5">
                              {citations.map((cit: any, i: number) => {
                                const hasPage =
                                  cit.page_start !== null &&
                                  cit.page_start !== undefined &&
                                  cit.page_start !== 0;

                                const pageText = hasPage
                                  ? cit.page_start === cit.page_end
                                    ? `第 ${cit.page_start} 页`
                                    : `第 ${cit.page_start}-${cit.page_end} 页`
                                  : "";

                                return (
                                  <li key={i} className="flex items-start gap-2 text-xs">
                                    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-md bg-primary/20 text-[10px] font-semibold text-primary">
                                      {i + 1}
                                    </span>
                                    <div className="min-w-0 flex-1">
                                      <div className="truncate text-muted/90">
                                        {cit.document_name || "未知文档"}
                                      </div>
                                      {hasPage && (
                                        <div className="mt-0.5 text-[11px] text-primary/70">{pageText}</div>
                                      )}
                                    </div>
                                  </li>
                                );
                              })}
                            </ul>
                          )}
                        </div>
                      );
                    })()}

                    {msg.role === "assistant" && (
                      <div
                        className={`flex items-center justify-between ${
                          msg.citations && msg.citations.length > 0
                            ? "mt-3"
                            : "mt-4 border-t border-glass-border pt-3"
                        }`}
                      >
                        <button
                          onClick={() => handleCopyAnswer(msg.content)}
                          className="flex items-center gap-1.5 rounded-md px-2.5 py-1 text-[11px] text-muted transition hover:bg-white/10 hover:text-text"
                          title="复制回答"
                        >
                          {copiedId === msg.id ? (
                            <>
                              <Check className="h-3.5 w-3.5 text-green-400" />
                              <span className="font-medium text-green-400">已复制</span>
                            </>
                          ) : (
                            <>
                              <Copy className="h-3.5 w-3.5" />
                              <span>复制回答</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-500 to-orange-500">
                      <User className="h-4 w-4 text-white" />
                    </div>
                  )}
                </div>
              ))
            )}

            {sending && (
              <div className="animate-fade-in flex gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary to-secondary">
                  <Bot className="h-4 w-4 text-white" />
                </div>
                <div className="glass rounded-2xl px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                      <span className="h-2 w-2 animate-bounce rounded-full bg-primary" style={{ animationDelay: "0ms" }}></span>
                      <span className="h-2 w-2 animate-bounce rounded-full bg-secondary" style={{ animationDelay: "150ms" }}></span>
                      <span className="h-2 w-2 animate-bounce rounded-full bg-accent" style={{ animationDelay: "300ms" }}></span>
                    </div>
                    <span className="text-sm text-muted">正在思考...</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSend} className="border-t border-glass-border/50 p-4">
            <div className="flex items-end gap-3">
              <div className="relative flex-1">
                <textarea
                  className="min-h-[60px] max-h-[120px] w-full resize-none rounded-xl border border-glass-border bg-white/5 p-4 pr-12 text-sm text-text outline-none transition-all duration-300 placeholder:text-muted focus:border-primary/50 focus:bg-white/10"
                  placeholder="请输入问题，按 Enter 发送，Shift + Enter 换行..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      handleSend(e);
                    }
                  }}
                  disabled={sending}
                  rows={2}
                />
              </div>
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="btn-gradient self-end flex items-center gap-2 rounded-xl px-6 py-3.5 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
              >
                {sending ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    发送中
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    发送
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </main>
    </Shell>
  );
}
