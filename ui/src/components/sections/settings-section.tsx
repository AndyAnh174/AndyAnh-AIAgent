"use client";

import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { useState, useEffect } from "react";
import { Save, Check, AlertCircle, RefreshCw, Loader2 } from "lucide-react";

export function SettingsSection() {
  const [apiKey, setApiKey] = useState("");
  const [apiUrl, setApiUrl] = useState("");
  const [ollamaBaseUrl, setOllamaBaseUrl] = useState("");
  const [ollamaVisionModel, setOllamaVisionModel] = useState("");
  const [ollamaModels, setOllamaModels] = useState<Array<{ name: string; model: string }>>([]);
  const [isLoadingModels, setIsLoadingModels] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [status, setStatus] = useState<{
    type: "success" | "error" | null;
    message: string;
  }>({ type: null, message: "" });

  useEffect(() => {
    // Load saved API key
    const savedKey = apiClient.getApiKey();
    if (savedKey) {
      setApiKey(savedKey);
    }

    // Load API URL from env or localStorage
    const savedUrl =
      typeof window !== "undefined"
        ? localStorage.getItem("api_url") ||
          process.env.NEXT_PUBLIC_API_URL ||
          "http://localhost:8000"
        : "http://localhost:8000";
    setApiUrl(savedUrl);

    // Load Ollama settings
    const savedOllamaUrl = apiClient.getOllamaBaseUrl();
    setOllamaBaseUrl(savedOllamaUrl);

    const savedOllamaModel = apiClient.getOllamaVisionModel();
    if (savedOllamaModel) {
      setOllamaVisionModel(savedOllamaModel);
    } else {
      setOllamaVisionModel("qwen2.5vl:7b"); // Default
    }

    // Load Ollama models
    loadOllamaModels(savedOllamaUrl);
  }, []);

  const loadOllamaModels = async (url?: string) => {
    setIsLoadingModels(true);
    try {
      const models = await apiClient.listOllamaModels(url);
      setOllamaModels(models);
    } catch (error) {
      console.error("Failed to load Ollama models:", error);
      setStatus({
        type: "error",
        message: "Không thể tải model Ollama. Hãy kiểm tra lại Ollama Base URL.",
      });
    } finally {
      setIsLoadingModels(false);
    }
  };

  const testConnection = async () => {
    try {
      await apiClient.healthCheck();
      setStatus({
        type: "success",
        message: "Kết nối API thành công!",
      });
    } catch (error) {
      setStatus({
        type: "error",
        message:
          error instanceof Error
            ? error.message
            : "Không thể kết nối tới API",
      });
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    setStatus({ type: null, message: "" });

    try {
      if (apiKey) {
        apiClient.setApiKey(apiKey);
      }

      if (apiUrl) {
        if (typeof window !== "undefined") {
          localStorage.setItem("api_url", apiUrl);
        }
      }

      // Save Ollama settings
      if (ollamaBaseUrl) {
        apiClient.setOllamaBaseUrl(ollamaBaseUrl);
      }
      if (ollamaVisionModel) {
        apiClient.setOllamaVisionModel(ollamaVisionModel);
      }

      // Test connection
      await testConnection();
    } catch (error) {
      setStatus({
        type: "error",
        message: "Không thể lưu cấu hình",
      });
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <section className="w-full max-w-3xl mx-auto px-4 py-6 md:py-10">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Cài đặt</h1>
          <p className="text-muted-foreground mt-2">
            Thiết lập kết nối API và các tùy chỉnh cho hệ thống
          </p>
        </div>

        <div className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="apiUrl" className="text-sm font-medium">
              API Base URL
            </label>
            <input
              id="apiUrl"
              type="url"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background font-mono text-sm"
              placeholder="http://localhost:8000"
            />
            <p className="text-xs text-muted-foreground">
              Địa chỉ API của AI Life Companion (backend)
            </p>
          </div>

          <div className="space-y-2">
            <label htmlFor="apiKey" className="text-sm font-medium">
              API Key
            </label>
            <input
              id="apiKey"
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background font-mono text-sm"
              placeholder="Nhập API key"
            />
            <p className="text-xs text-muted-foreground">
              API key dùng để xác thực. Định nghĩa trong file .env backend với biến API_KEYS
            </p>
          </div>

          <div className="border-t border-border pt-6 space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Cấu hình Ollama</h2>
              <p className="text-sm text-muted-foreground">
                Thiết lập Ollama cho xử lý hình ảnh, PDF và video
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="ollamaBaseUrl" className="text-sm font-medium">
                Ollama Base URL
              </label>
              <div className="flex gap-2">
                <input
                  id="ollamaBaseUrl"
                  type="url"
                  value={ollamaBaseUrl}
                  onChange={(e) => setOllamaBaseUrl(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-md border border-input bg-background font-mono text-sm"
                  placeholder="http://222.253.80.30:11434"
                />
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => loadOllamaModels(ollamaBaseUrl)}
                  disabled={isLoadingModels}
                >
                  {isLoadingModels ? (
                    <Loader2 className="size-4 animate-spin" />
                  ) : (
                    <RefreshCw className="size-4" />
                  )}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Địa chỉ server Ollama của bạn
              </p>
            </div>

            <div className="space-y-2">
              <label htmlFor="ollamaVisionModel" className="text-sm font-medium">
                Model Ollama cho thị giác
              </label>
              <div className="flex gap-2">
                <select
                  id="ollamaVisionModel"
                  value={ollamaVisionModel}
                  onChange={(e) => setOllamaVisionModel(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-md border border-input bg-background"
                  disabled={ollamaModels.length === 0}
                >
                  {ollamaModels.length === 0 ? (
                    <option value="">Đang tải danh sách model...</option>
                  ) : (
                    <>
                      <option value="qwen2.5vl:7b">qwen2.5vl:7b (Mặc định)</option>
                      {ollamaModels
                        .filter((m) => m.name !== "qwen2.5vl:7b")
                        .map((model) => (
                          <option key={model.name} value={model.name}>
                            {model.name}
                          </option>
                        ))}
                    </>
                  )}
                </select>
                <input
                  type="text"
                  value={ollamaVisionModel}
                  onChange={(e) => setOllamaVisionModel(e.target.value)}
                  className="flex-1 px-3 py-2 rounded-md border border-input bg-background font-mono text-sm"
                  placeholder="Hoặc nhập thủ công tên model"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                Model Ollama dùng cho nhiệm vụ thị giác. Mặc định: qwen2.5vl:7b
              </p>
            </div>
          </div>

          {status.type && (
            <div
              className={`flex items-center gap-2 p-4 rounded-lg border ${
                status.type === "success"
                  ? "bg-green-500/10 border-green-500/20 text-green-600 dark:text-green-400"
                  : "bg-destructive/10 border-destructive/20 text-destructive"
              }`}
            >
              {status.type === "success" ? (
                <Check className="size-4" />
              ) : (
                <AlertCircle className="size-4" />
              )}
              <p className="text-sm">{status.message}</p>
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving ? (
                "Đang lưu..."
              ) : (
                <>
                  <Save className="size-4 mr-2" />
                  Lưu & Kiểm tra kết nối
                </>
              )}
            </Button>
            <Button variant="outline" onClick={testConnection}>
              Kiểm tra kết nối
            </Button>

            <Button
              variant="destructive"
              onClick={async () => {
                if (!confirm("⚠️ Bạn có chắc muốn xóa TẤT CẢ dữ liệu? Hành động này không thể hoàn tác!")) {
                  return;
                }
                if (!confirm("Xác nhận lần cuối: Xóa tất cả journal entries và media?")) {
                  return;
                }
                
                try {
                  setIsSaving(true);
                  await apiClient.clearAllData(true);
                  setStatus({
                    type: "success",
                    message: "Đã xóa tất cả dữ liệu thành công.",
                  });
                } catch (err) {
                  setStatus({
                    type: "error",
                    message: err instanceof Error ? err.message : "Không thể xóa dữ liệu.",
                  });
                } finally {
                  setIsSaving(false);
                }
              }}
              disabled={isSaving}
            >
              Xóa toàn bộ dữ liệu
            </Button>
          </div>
        </div>

        <div className="mt-8 bg-muted/50 border border-border rounded-lg p-6">
          <h3 className="font-semibold mb-2">Gợi ý cấu hình</h3>
          <div className="text-sm text-muted-foreground space-y-2">
            <p>
              Để thiết lập API key, thêm vào file .env của backend:
            </p>
            <pre className="bg-background p-3 rounded border border-border text-xs overflow-x-auto">
              API_KEYS=your-api-key-here
            </pre>
            <p className="mt-4">
              Có thể định nghĩa nhiều API key, cách nhau bởi dấu phẩy:
            </p>
            <pre className="bg-background p-3 rounded border border-border text-xs overflow-x-auto">
              API_KEYS=key1,key2,key3
            </pre>
          </div>
        </div>
      </div>
    </section>
  );
}
