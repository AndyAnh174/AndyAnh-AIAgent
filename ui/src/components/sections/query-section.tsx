"use client";

import { Button } from "@/components/ui/button";
import { apiClient, type RetrievalRequest } from "@/lib/api";
import { useState, useEffect, useRef } from "react";
import { Send, Loader2, Sparkles, Settings2, ChevronDown, ChevronUp, AlertCircle } from "lucide-react";
import Link from "next/link";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  references?: Array<{ entry_id: number; tags: string[] }>;
  searchResults?: {
    query: string;
    count: number;
    results: Array<{
      entry_id: number;
      title: string;
      content: string;
      mood?: string;
      tags: string[];
      created_at: string;
      media: Array<{
        id: number;
        type: string;
        url: string;
        storage_path: string;
        details: Record<string, unknown>;
      }>;
    }>;
  } | null;
  timestamp: Date;
}

export function QuerySection() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [topK, setTopK] = useState(5);
  const [mode, setMode] = useState<"graph" | "hybrid">("graph");
  const [model, setModel] = useState<"gemini" | "openai" | "ollama" | null>(null);
  const [ollamaModel, setOllamaModel] = useState<string>("");
  const [ollamaModels, setOllamaModels] = useState<Array<{ name: string; model: string }>>([]);
  const [isLoadingOllamaModels, setIsLoadingOllamaModels] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Check API key on mount
  useEffect(() => {
    const checkApiKey = () => {
      const apiKey = apiClient.getApiKey();
      if (!apiKey) {
        setError("Chưa cấu hình API key. Hãy thiết lập trong mục Cài đặt.");
      } else {
        setError(null);
      }
    };
    
    checkApiKey();
    // Check periodically in case user updates it in another tab
    const interval = setInterval(checkApiKey, 2000);
    return () => clearInterval(interval);
  }, []);

  // Auto-scroll to bottom when new message arrives
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Load Ollama models when Ollama is selected
  useEffect(() => {
    if (model === "ollama") {
      loadOllamaModels();
    }
  }, [model]);

  const loadOllamaModels = async () => {
    setIsLoadingOllamaModels(true);
    try {
      const models = await apiClient.listOllamaModels();
      setOllamaModels(models);
      // Set default model if available
      const defaultModel = models.find(m => m.name.includes("qwen") || m.name.includes("llama"))?.name || models[0]?.name || "";
      if (defaultModel) {
        setOllamaModel(defaultModel);
      }
    } catch (error) {
      console.error("Failed to load Ollama models:", error);
      setError("Không thể tải danh sách model Ollama. Kiểm tra lại Ollama Base URL trong Cài đặt.");
    } finally {
      setIsLoadingOllamaModels(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim().length < 3) {
      setError("Câu hỏi phải có ít nhất 3 ký tự");
      return;
    }

    const apiKey = apiClient.getApiKey();
    if (!apiKey) {
      setError("Cần có API key. Vui lòng cấu hình trong trang Cài đặt.");
      return;
    }

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input.trim(),
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setError(null);
    setIsLoading(true);

    try {
      const request: RetrievalRequest = {
        query: input.trim(),
        top_k: topK,
        mode,
        model: model || undefined,
        ollama_model: model === "ollama" && ollamaModel ? ollamaModel : undefined,
      };

      const response = await apiClient.queryJournal(request);
      
      // Check for function calls in response
      const functionCallRegex = /\[FUNCTION_CALL:([^\]]+)\]([\s\S]*?)\[\/FUNCTION_CALL\]/g;
      let processedAnswer = response.answer;
      let searchResults: {
        query: string;
        count: number;
        results: Array<{
          entry_id: number;
          title: string;
          content: string;
          mood?: string;
          tags: string[];
          created_at: string;
          media: Array<{
            id: number;
            type: string;
            url: string;
            storage_path: string;
            details: Record<string, unknown>;
          }>;
        }>;
      } | null = null;
      
      const functionCalls = Array.from(response.answer.matchAll(functionCallRegex));
      if (functionCalls.length > 0) {
        // Process first function call (usually /search)
        const call = functionCalls[0];
        const functionName = call[1];
        const functionParams = call[2];
        
        if (functionName === "/search") {
          // Parse parameters
          const params: { query: string; has_media?: boolean; media_type?: string } = { query: "" };
          const paramLines = functionParams.split("\n");
          for (const line of paramLines) {
            if (line.includes(":")) {
              const [key, value] = line.split(":").map(s => s.trim());
              if (key === "query") params.query = value;
              if (key === "has_media") params.has_media = value === "true";
              if (key === "media_type") params.media_type = value;
            }
          }
          
          // Call search API
          try {
            searchResults = await apiClient.searchEntries({
              query: params.query || input.trim(),
              has_media: params.has_media,
              media_type: params.media_type as "image" | "video" | "pdf" | undefined,
            });
            
            // Remove function call from answer and append search results
            processedAnswer = response.answer.replace(functionCallRegex, "");
            if (searchResults.count > 0) {
              processedAnswer += "\n\n**Kết quả tìm kiếm:**\n";
              for (const result of searchResults.results) {
                processedAnswer += `\nNhật ký #${result.entry_id}: ${result.title}\n`;
                if (result.media.length > 0) {
                  processedAnswer += "Tệp đính kèm:\n";
                  for (const media of result.media) {
                    const mediaUrl = apiClient.getMediaUrl(media.id);
                    processedAnswer += `- [${media.type}] ${mediaUrl}\n`;
                  }
                }
              }
            }
          } catch (searchErr) {
            console.error("Search failed:", searchErr);
            processedAnswer += "\n\n⚠️ Không thể tìm kiếm. Vui lòng thử lại.";
          }
        }
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: processedAnswer,
        references: response.references,
        searchResults: searchResults,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      // Extract error message properly
      let errorMessage = "Không thể truy vấn nhật ký";
      if (err instanceof Error) {
        errorMessage = err.message;
      } else if (typeof err === "string") {
        errorMessage = err;
      } else if (err && typeof err === "object") {
        // Try to extract message from error object
        const errObj = err as Record<string, unknown>;
        errorMessage = (errObj.message as string) || (errObj.detail as string) || ((errObj.error as { message?: string })?.message) || JSON.stringify(err);
      }
      
      setError(errorMessage);
      
      const errorMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `Lỗi: ${errorMessage}`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <section className="flex flex-col h-[calc(100vh-120px)] max-w-6xl mx-auto px-4 py-4">
      {/* Header */}
      <div className="mb-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold flex items-center gap-2">
              <Sparkles className="size-5" />
              Truy vấn nhật ký
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Đặt câu hỏi về những gì bạn đã ghi lại thông qua GraphRAG
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
            className="flex items-center gap-2"
          >
            <Settings2 className="size-4" />
            {showSettings ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
            Thiết lập
          </Button>
        </div>

        {/* Settings Panel */}
        {showSettings && (
          <div className="mt-4 bg-muted/50 border border-border rounded-lg p-4 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-2">
                <label htmlFor="topK" className="text-xs font-medium">
                  Số kết quả (Top K)
                </label>
                <input
                  id="topK"
                  type="number"
                  min={1}
                  max={20}
                  value={topK}
                  onChange={(e) => setTopK(Number(e.target.value))}
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="mode" className="text-xs font-medium">
                  Chế độ
                </label>
                <select
                  id="mode"
                  value={mode}
                  onChange={(e) => setMode(e.target.value as "graph" | "hybrid")}
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background"
                >
                  <option value="graph">Đồ thị</option>
                  <option value="hybrid">Kết hợp</option>
                </select>
              </div>

              <div className="space-y-2">
                <label htmlFor="model" className="text-xs font-medium">
                  Mô hình
                </label>
                <select
                  id="model"
                  value={model || ""}
                  onChange={(e) =>
                    setModel(
                      e.target.value
                        ? (e.target.value as "gemini" | "openai" | "ollama")
                        : null,
                    )
                  }
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background"
                >
                  <option value="">Mặc định</option>
                  <option value="gemini">Gemini</option>
                  <option value="openai">OpenAI</option>
                  <option value="ollama">Ollama</option>
                </select>
              </div>
            </div>
            
            {/* Ollama Model Selector */}
            {model === "ollama" && (
              <div className="space-y-2 border-t border-border pt-4">
                <label htmlFor="ollamaModel" className="text-xs font-medium">
                  Model Ollama
                </label>
                {isLoadingOllamaModels ? (
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <Loader2 className="size-3 animate-spin" />
                    Đang tải danh sách model...
                  </div>
                ) : (
                  <select
                    id="ollamaModel"
                    value={ollamaModel}
                    onChange={(e) => setOllamaModel(e.target.value)}
                    className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background"
                  >
                    {ollamaModels.length === 0 ? (
                      <option value="">Không có model khả dụng</option>
                    ) : (
                      ollamaModels.map((m) => (
                        <option key={m.name} value={m.name}>
                          {m.name}
                        </option>
                      ))
                    )}
                  </select>
                )}
                <p className="text-xs text-muted-foreground">
                  Chọn model Ollama cho truy vấn văn bản
                </p>
              </div>
            )}
            
            <div className="text-xs text-muted-foreground">
              <strong>Lưu ý:</strong> Tính năng thị giác luôn sử dụng Ollama qwen2.5vl:7b
            </div>
          </div>
        )}
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto space-y-4 mb-4 pr-2">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center space-y-2 text-muted-foreground">
              <Sparkles className="size-12 mx-auto opacity-50" />
              <p className="text-lg">Bắt đầu cuộc trò chuyện</p>
              <p className="text-sm">Hỏi lại những điều bạn từng viết trong nhật ký</p>
            </div>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted border border-border"
              }`}
            >
              <div className="text-sm leading-relaxed break-words space-y-2 markdown-content">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
              
              {message.references && message.references.length > 0 && (
                <div className="mt-3 pt-3 border-t border-border/50">
                  <p className="text-xs font-medium mb-2 opacity-70">Tham chiếu:</p>
                  <div className="space-y-1">
                    {message.references.map((ref, idx) => (
                      <div key={idx} className="text-xs opacity-60">
                        Nhật ký #{ref.entry_id}
                        {ref.tags.length > 0 && ` • ${ref.tags.join(", ")}`}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {message.searchResults && message.searchResults.count > 0 && (
                <div className="mt-3 pt-3 border-t border-border/50">
                  <p className="text-xs font-medium mb-2 opacity-70">
                    Tìm thấy {message.searchResults.count} kết quả:
                  </p>
                  <div className="space-y-3">
                    {message.searchResults.results.map((result) => (
                      <div key={result.entry_id} className="bg-muted/30 rounded-lg p-3 border border-border/50">
                        <p className="text-sm font-medium mb-1">
                          Nhật ký #{result.entry_id}: {result.title}
                        </p>
                        <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                          {result.content}
                        </p>
                        {result.media.length > 0 && (
                          <div className="mt-2">
                            <p className="text-xs font-medium mb-1">Tệp đính kèm:</p>
                            <div className="flex flex-wrap gap-2">
                              {result.media.map((media) => {
                                const mediaUrl = apiClient.getMediaUrl(media.id);
                                return (
                                  <a
                                    key={media.id}
                                    href={mediaUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    download
                                    className="text-xs px-2 py-1 rounded bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors"
                                  >
                                    📎 {media.type} (Tải xuống)
                                  </a>
                                );
                              })}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <p className="text-xs opacity-50 mt-2">
                {message.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-muted border border-border rounded-lg px-4 py-3">
              <Loader2 className="size-4 animate-spin" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3 mb-4 flex items-center gap-2">
          <AlertCircle className="size-4 text-destructive shrink-0" />
          <p className="text-sm text-destructive flex-1">{error}</p>
          {error.includes("API key") && (
            <Button asChild variant="outline" size="sm">
              <Link href="/settings">Tới trang Cài đặt</Link>
            </Button>
          )}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="border-t border-border pt-4">
        <div className="flex gap-2">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Đặt câu hỏi về nhật ký của bạn..."
            rows={1}
            className="flex-1 px-4 py-3 rounded-lg border border-input bg-background resize-none focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={isLoading || input.trim().length < 3}
            size="lg"
            className="shrink-0"
          >
            {isLoading ? (
              <Loader2 className="size-4 animate-spin" />
            ) : (
              <Send className="size-4" />
            )}
          </Button>
        </div>
        <p className="text-xs text-muted-foreground mt-2">
          Nhấn Enter để gửi, Shift + Enter để xuống dòng
        </p>
      </form>
    </section>
  );
}