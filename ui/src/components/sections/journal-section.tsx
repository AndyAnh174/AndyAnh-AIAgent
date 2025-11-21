"use client";

import { Button } from "@/components/ui/button";
import { apiClient, type CreateJournalRequest } from "@/lib/api";
import { useState } from "react";
import { Upload, X, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";

export function JournalSection() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [mood, setMood] = useState("");
  const [tags, setTags] = useState("");
  const [media, setMedia] = useState<Array<{ type: string; url: string; caption?: string; file?: File }>>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (event) => {
        const result = event.target?.result as string;
        let type: "image" | "video" | "pdf" = "image";
        
        if (file.type.startsWith("image/")) type = "image";
        else if (file.type.startsWith("video/")) type = "video";
        else if (file.type === "application/pdf") type = "pdf";

        setMedia((prev) => [
          ...prev,
          {
            type,
            url: result,
            caption: "",
            file,
          },
        ]);
      };
      reader.readAsDataURL(file);
    });
  };

  const removeMedia = (index: number) => {
    setMedia((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      const request: CreateJournalRequest = {
        title,
        content,
        mood: mood || undefined,
        tags: tags
          ? tags.split(",").map((t) => t.trim()).filter(Boolean)
          : undefined,
        media: media.map((m) => ({
          type: m.type as "image" | "video" | "pdf",
          url: m.url,
          caption: m.caption || undefined,
        })),
      };

      const response = await apiClient.createJournalEntry(request);
      // Reset form on success
      setTitle("");
      setContent("");
      setMood("");
      setTags("");
      setMedia([]);
      // Show success message
      alert(`Tạo nhật ký thành công! ID: ${response.entry_id}`);
      router.push("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tạo nhật ký");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <section className="w-full max-w-4xl mx-auto px-4 py-12">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold">Tạo nhật ký mới</h1>
          <p className="text-muted-foreground mt-2">
            Ghi lại suy nghĩ, ký ức và trải nghiệm của bạn với khả năng trích xuất nội dung bằng AI
          </p>
          <div className="mt-4 bg-muted/50 border border-border rounded-lg p-4">
            <p className="text-sm text-muted-foreground">
              <strong>Xử lý AI:</strong> Ảnh, PDF và video sẽ được Ollama qwen2.5vl:7b xử lý tự động để trích xuất nội dung và thêm vào nhật ký.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium">
              Tiêu đề *
            </label>
            <input
              id="title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background"
              placeholder="Bạn đang nghĩ gì?"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="content" className="text-sm font-medium">
              Nội dung *
            </label>
            <textarea
              id="content"
              required
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={8}
              className="w-full px-3 py-2 rounded-md border border-input bg-background resize-none"
              placeholder="Viết nhật ký của bạn tại đây..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="mood" className="text-sm font-medium">
                Tâm trạng
              </label>
              <input
                id="mood"
                type="text"
                value={mood}
                onChange={(e) => setMood(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-input bg-background"
                placeholder="vui, buồn, hào hứng..."
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="tags" className="text-sm font-medium">
                Thẻ (phân tách bằng dấu phẩy)
              </label>
              <input
                id="tags"
                type="text"
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                className="w-full px-3 py-2 rounded-md border border-input bg-background"
                placeholder="công việc, cá nhân, du lịch..."
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium">Tệp đính kèm (Ảnh, Video, PDF)</label>
            <div className="border-2 border-dashed border-border rounded-lg p-6">
              <input
                type="file"
                id="media-upload"
                multiple
                accept="image/*,video/*,application/pdf"
                onChange={handleFileUpload}
                className="hidden"
              />
              <label
                htmlFor="media-upload"
                className="flex flex-col items-center justify-center cursor-pointer"
              >
                <Upload className="size-8 text-muted-foreground mb-2" />
                <span className="text-sm text-muted-foreground">
                  Nhấn để tải lên hoặc kéo thả vào đây
                </span>
              </label>
            </div>

            {media.length > 0 && (
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
                {media.map((item, index) => (
                  <div
                    key={index}
                    className="relative group rounded-lg overflow-hidden border border-border"
                  >
                    {item.type === "image" && (
                      <img
                        src={item.url}
                        alt={item.caption || `Media ${index + 1}`}
                        className="w-full h-32 object-cover"
                      />
                    )}
                    {item.type === "video" && (
                      <video
                        src={item.url}
                        className="w-full h-32 object-cover"
                        controls
                      />
                    )}
                    {item.type === "pdf" && (
                      <div className="w-full h-32 bg-muted flex items-center justify-center">
                        <span className="text-sm">Tệp PDF</span>
                      </div>
                    )}
                    <button
                      type="button"
                      onClick={() => removeMedia(index)}
                      className="absolute top-2 right-2 bg-destructive text-destructive-foreground rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                      <X className="size-4" />
                    </button>
                    <input
                      type="text"
                      value={item.caption || ""}
                      onChange={(e) => {
                        const newMedia = [...media];
                        newMedia[index].caption = e.target.value;
                        setMedia(newMedia);
                      }}
                      placeholder="Chú thích (không bắt buộc)"
                      className="absolute bottom-0 left-0 right-0 p-2 bg-black/50 text-white text-xs"
                    />
                  </div>
                ))}
              </div>
            )}
          </div>

          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          <div className="flex gap-4">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? (
                <>
                  <Loader2 className="size-4 mr-2 animate-spin" />
                  Đang tạo...
                </>
              ) : (
                "Lưu nhật ký"
              )}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.push("/")}
            >
              Hủy
            </Button>
          </div>
        </form>
      </div>
    </section>
  );
}
