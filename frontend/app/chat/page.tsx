"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Shell, Sidebar, Badge } from "@/components/ui";
import { api, getToken, clearToken } from "@/lib/api";
import type { Conversation, Message, KnowledgeBase } from "@/lib/api";
import { Send, Plus, Sparkles, User, Bot, MessageSquare, ChevronDown, Trash2, MoreHorizontal, Copy, Check } from "lucide-react";
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
      setError(err.message || "创建失败");
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
      setError(err.message || "删除失败");
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
            prev.map((m) =>
              m.id === "temp-assistant"
                ? { ...m, citations }
                : m
            )
          );
        } else if (event.type === "delta") {
          fullContent += event.content;
          setMessages((prev) =>
            prev.map((m) =>
              m.id === "temp-assistant"
                ? { ...m, content: fullContent }
                : m
            )
          );
        } else if (event.type === "done") {
          finalUsage = event.usage || {};
          setMessages((prev) =>
            prev.map((m) =>
              m.id === "temp-assistant"
                ? { ...m, usage: finalUsage }
                : m
            )
          );
        } else if (event.type === "error") {
          throw new Error(event.message || "生成失败");
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

  if (loading) {
    return (
      <Shell>
        <Sidebar />
        <main className="flex-1">
          <div className="rounded-2xl glass shadow-glass p-8">
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
      <main className="flex-1 flex gap-6 h-[calc(100vh-3rem)]">
        <div className="w-64 shrink-0 space-y-4">
          <div className="space-y-3">
            <div className="relative group">
              <select
                value={selectedKb}
                onChange={(e) => setSelectedKb(e.target.value)}
                className="w-full appearance-none rounded-xl border border-glass-border bg-bg-secondary/80 px-4 py-2.5 pr-10 text-sm outline-none transition-all duration-300 focus:border-primary/50 focus:bg-bg-secondary text-text cursor-pointer hover:border-glass-border/80"
              >
                {kbs.map((kb) => (
                  <option key={kb.id} value={kb.id} className="bg-bg-secondary text-text">
                    {kb.name}
                  </option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted pointer-events-none transition-transform group-hover:text-text" />
            </div>
            <button
              onClick={handleNewConversation}
              className="w-full btn-gradient rounded-xl px-4 py-2.5 text-sm font-medium text-white flex items-center justify-center gap-2"
            >
              <Plus className="w-4 h-4" />
              新对话
            </button>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400 animate-fade-in">
              {error}
            </div>
          )}

          <div className="glass rounded-2xl p-4 shadow-glass">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <MessageSquare className="w-4 h-4 text-primary" />
                <span className="text-xs uppercase tracking-[0.15em] text-muted font-medium">对话列表</span>
              </div>
              <span className="text-xs text-muted">{filteredConversations.length}</span>
            </div>
            <div className="space-y-1 max-h-[55vh] overflow-y-auto scrollbar-thin pr-1">
              {filteredConversations.length === 0 ? (
                <div className="text-xs text-muted py-4 text-center">暂无对话</div>
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
                      className={`w-full text-left px-3 py-2.5 text-sm transition-all duration-200 ${
                        currentConv?.id === conv.id
                          ? "text-white"
                          : "text-muted hover:text-text"
                      }`}
                    >
                      <div className="truncate font-medium pr-8">{conv.title}</div>
                    </button>
                    <button
                      onClick={(e) => handleDeleteConversation(conv.id, e)}
                      className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg opacity-0 group-hover:opacity-100 transition-all duration-200 hover:bg-red-500/20 text-muted hover:text-red-400"
                      title="删除对话"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col rounded-2xl glass shadow-glass overflow-hidden">
          <div className="border-b border-glass-border/50 px-6 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-primary" />
                  {currentConv ? currentConv.title : "知识库问答"}
                </h2>
                <p className="mt-0.5 text-sm text-muted">
                  支持流式输出和引用展示
                </p>
              </div>
              {selectedKb && (
                <Badge variant="primary">
                  {kbs.find(k => k.id === selectedKb)?.name || "已选知识库"}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin">
            {loadingMessages ? (
              <div className="h-full flex items-center justify-center">
                <div className="flex items-center gap-3 text-muted">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
                  <span>加载消息中...</span>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-muted">
                <div className="text-center">
                  <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-primary/20 to-secondary/10 flex items-center justify-center mx-auto mb-4">
                    <Sparkles className="w-8 h-8 text-primary" />
                  </div>
                  <p className="text-lg font-semibold text-text">开始新的对话</p>
                  <p className="mt-2 text-sm text-muted max-w-sm">
                    选择知识库后，在下方输入问题开始智能问答
                  </p>
                </div>
              </div>
            ) : (
              messages.map((msg, index) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"} animate-fade-in-up`}
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {msg.role === "assistant" && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shrink-0">
                      <Bot className="w-4 h-4 text-white" />
                    </div>
                  )}
                  <div
                    className={`max-w-[75%] rounded-2xl px-5 py-4 ${
                      msg.role === "user"
                        ? "bg-gradient-to-br from-primary to-secondary text-white shadow-lg shadow-primary/20"
                        : "glass shadow-sm text-text"
                    }`}
                  >
                    {msg.role === "assistant" ? (
                      <MarkdownMessage content={cleanAnswerContent(msg.content)} />
                    ) : (
                      <p className="whitespace-pre-wrap text-sm leading-relaxed">
                        {msg.content}
                      </p>
                    )}
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-glass-border">
                        <p className="text-xs font-medium mb-2 text-muted">引用来源：</p>
                        <ul className="space-y-1.5">
                          {(() => {
                            const seen = new Set<string>();
                            const unique = msg.citations.filter((cit: any) => {
                              const key = `${cit.document_name || "未知文档"}-${cit.page_start || ""}-${cit.page_end || ""}`;
                              if (seen.has(key)) return false;
                              seen.add(key);
                              return true;
                            });
                            return unique.slice(0, 5).map((cit: any, i: number) => {
                              const hasPage = cit.page_start !== null && cit.page_start !== undefined && cit.page_start !== 0;
                              let pageText = "";
                              if (hasPage) {
                                if (cit.page_start === cit.page_end) {
                                  pageText = `第 ${cit.page_start} 页`;
                                } else {
                                  pageText = `第 ${cit.page_start}-${cit.page_end} 页`;
                                }
                              }
                              return (
                                <li key={i} className="text-xs flex items-start gap-2">
                                  <span className="w-5 h-5 rounded-md bg-primary/20 text-primary flex items-center justify-center shrink-0 text-[10px] font-semibold">
                                    {i + 1}
                                  </span>
                                  <div className="flex-1 min-w-0">
                                    <div className="text-muted/90 truncate">{cit.document_name || "未知文档"}</div>
                                    {hasPage && (
                                      <div className="text-[11px] text-primary/70 mt-0.5">{pageText}</div>
                                    )}
                                  </div>
                                </li>
                              );
                            });
                          })()}
                        </ul>
                      </div>
                    )}
                    {msg.role === "assistant" && (
                      <div className={`flex items-center justify-between ${msg.citations && msg.citations.length > 0 ? "mt-3" : "mt-4 pt-3 border-t border-glass-border"}`}>
                        <button
                          onClick={() => handleCopyAnswer(msg.content)}
                          className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] rounded-md text-muted hover:text-text hover:bg-white/10 transition"
                          title="复制回答"
                        >
                          {copiedId === msg.id ? (
                            <>
                              <Check className="w-3.5 h-3.5 text-green-400" />
                              <span className="text-green-400 font-medium">已复制</span>
                            </>
                          ) : (
                            <>
                              <Copy className="w-3.5 h-3.5" />
                              <span>复制回答</span>
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                  {msg.role === "user" && (
                    <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shrink-0">
                      <User className="w-4 h-4 text-white" />
                    </div>
                  )}
                </div>
              ))
            )}
            {sending && (
              <div className="flex gap-3 animate-fade-in">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-primary to-secondary flex items-center justify-center shrink-0">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="glass rounded-2xl px-5 py-4">
                  <div className="flex items-center gap-3">
                    <div className="flex gap-1.5">
                      <span className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                      <span className="w-2 h-2 bg-secondary rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                      <span className="w-2 h-2 bg-accent rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                    </div>
                    <span className="text-sm text-muted">思考中...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSend} className="border-t border-glass-border/50 p-4">
            <div className="flex gap-3 items-end">
              <div className="flex-1 relative">
                <textarea
                  className="w-full min-h-[60px] max-h-[120px] rounded-xl border border-glass-border bg-white/5 p-4 pr-12 outline-none resize-none transition-all duration-300 focus:border-primary/50 focus:bg-white/10 text-text placeholder:text-muted text-sm"
                  placeholder="请输入问题，按 Enter 发送，Shift+Enter 换行..."
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
                className="self-end btn-gradient rounded-xl px-6 py-3.5 font-medium text-white flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? (
                  <>
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    发送中
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
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
