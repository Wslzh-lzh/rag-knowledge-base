"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Shell, Sidebar, Card } from "@/components/ui";
import { api, getToken, clearToken } from "@/lib/api";
import type { Conversation, Message, KnowledgeBase } from "@/lib/api";

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

  useEffect(() => {
    if (!getToken()) {
      router.push("/login");
      return;
    }
    loadInitialData();
  }, [router]);

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
      }

      if (convsResp.length > 0) {
        setCurrentConv(convsResp[0]);
        setLoadingMessages(true);
        try {
          const msgs = await api.listMessages(convsResp[0].id);
          setMessages(msgs);
        } finally {
          setLoadingMessages(false);
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
      if (selectedKb) {
        const stream = api.askStream(selectedKb, userInput, 5);
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
          } else if (event.type === "error") {
            throw new Error(event.message || "生成失败");
          }
        }

        try {
          const savedMsg = await api.sendMessage(conv.id, userInput);
          setMessages((prev) =>
            prev.map((m) =>
              m.id === "temp-assistant"
                ? { ...savedMsg, content: fullContent, citations }
                : m
            )
          );
        } catch {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === "temp-assistant"
                ? { ...m, id: `assistant-${Date.now()}`, usage: finalUsage }
                : m
            )
          );
        }
      } else {
        const reply = await api.sendMessage(conv.id, userInput);
        setMessages((prev) => [...prev.filter((m) => m.id !== "temp-user" && m.id !== "temp-assistant"), reply]);
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
      <main className="flex-1 flex gap-6 h-[calc(100vh-3rem)]">
        <div className="w-64 shrink-0 space-y-3">
          <div className="space-y-2">
            <select
              value={selectedKb}
              onChange={(e) => setSelectedKb(e.target.value)}
              className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2 text-sm outline-none transition focus:border-accent/50"
            >
              <option value="">选择知识库</option>
              {kbs.map((kb) => (
                <option key={kb.id} value={kb.id}>
                  {kb.name}
                </option>
              ))}
            </select>
            <button
              onClick={handleNewConversation}
              className="w-full rounded-xl bg-accent px-4 py-2 text-sm font-medium text-slate-950 transition hover:opacity-90 disabled:opacity-50"
            >
              + 新对话
            </button>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-400">
              {error}
            </div>
          )}

          <div className="rounded-2xl border border-white/10 bg-panel/80 p-3 shadow-soft">
            <div className="mb-2 text-xs uppercase tracking-[0.2em] text-muted">对话列表</div>
            <div className="space-y-1 max-h-[55vh] overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="text-xs text-muted py-2 text-center">暂无对话</div>
              ) : (
                conversations.map((conv) => (
                  <button
                    key={conv.id}
                    onClick={() => handleSelectConversation(conv)}
                    className={`w-full text-left rounded-lg px-3 py-2 text-sm transition ${
                      currentConv?.id === conv.id
                        ? "bg-white/10 text-text"
                        : "text-muted hover:bg-white/5 hover:text-text"
                    }`}
                  >
                    <div className="truncate">{conv.title}</div>
                  </button>
                ))
              )}
            </div>
          </div>
        </div>

        <div className="flex-1 flex flex-col rounded-2xl border border-white/10 bg-panel/80 shadow-soft overflow-hidden">
          <div className="border-b border-white/10 px-5 py-4">
            <h2 className="text-lg font-semibold">
              {currentConv ? currentConv.title : "知识库问答"}
            </h2>
            <p className="mt-1 text-sm text-muted">
              支持流式输出和引用展示
            </p>
          </div>

          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {loadingMessages ? (
              <div className="h-full flex items-center justify-center">
                <div className="flex items-center gap-3 text-muted">
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-accent border-t-transparent"></div>
                  <span>加载消息中...</span>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="h-full flex items-center justify-center text-muted">
                <div className="text-center">
                  <p className="text-lg font-medium text-text">开始新的对话</p>
                  <p className="mt-2 text-sm">选择知识库后，在下方输入问题开始提问</p>
                </div>
              </div>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                      msg.role === "user"
                        ? "bg-accent text-slate-950"
                        : "border border-white/10 bg-white/5 text-text"
                    }`}
                  >
                    <p className="whitespace-pre-wrap text-sm">{msg.content}</p>
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-white/10">
                        <p className="text-xs font-medium mb-2">引用来源：</p>
                        <ul className="space-y-1">
                          {msg.citations.slice(0, 3).map((cit: any, i: number) => (
                            <li key={i} className="text-xs opacity-80">
                              [{i + 1}] {cit.document_name || "未知文档"}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
            {sending && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <div className="flex items-center gap-2 text-sm text-muted">
                    <div className="flex gap-1">
                      <span className="w-2 h-2 bg-muted rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></span>
                      <span className="w-2 h-2 bg-muted rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></span>
                      <span className="w-2 h-2 bg-muted rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></span>
                    </div>
                    <span className="ml-1">思考中...</span>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          <form onSubmit={handleSend} className="border-t border-white/10 p-4">
            <div className="flex gap-3">
              <textarea
                className="flex-1 min-h-[60px] max-h-[120px] rounded-xl border border-white/10 bg-white/5 p-3 outline-none resize-none transition focus:border-accent/50"
                placeholder="请输入问题..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend(e);
                  }
                }}
                disabled={sending}
              />
              <button
                type="submit"
                disabled={sending || !input.trim()}
                className="self-end rounded-xl bg-accent px-6 py-3 font-medium text-slate-950 transition hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {sending ? "发送中" : "发送"}
              </button>
            </div>
          </form>
        </div>
      </main>
    </Shell>
  );
}
