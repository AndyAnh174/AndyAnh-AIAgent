"use client";

import { Button } from "@/components/ui/button";
import { apiClient, type JournalEntrySummary, type JournalEntryDetail } from "@/lib/api";
import { useEffect, useState } from "react";
import { Loader2, RefreshCw, Trash2, Edit3, ImageIcon } from "lucide-react";

export function DataManagerSection() {
  const [entries, setEntries] = useState<JournalEntrySummary[]>([]);
  const [selectedEntry, setSelectedEntry] = useState<JournalEntryDetail | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadEntries = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.listJournalEntries({ limit: 100 });
      setEntries(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Không thể tải danh sách nhật ký";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadEntries();
  }, []);

  const handleSelectEntry = async (entryId: number) => {
    setError(null);
    try {
      const detail = await apiClient.getJournalEntry(entryId);
      setSelectedEntry(detail);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Không thể tải chi tiết nhật ký";
      setError(msg);
    }
  };

  const handleUpdateEntry = async () => {
    if (!selectedEntry) return;
    setIsSaving(true);
    setError(null);
    try {
      const updated = await apiClient.updateJournalEntry(selectedEntry.entry_id, {
        title: selectedEntry.title,
        content: selectedEntry.content,
        mood: selectedEntry.mood || undefined,
        tags: selectedEntry.tags,
      });
      setSelectedEntry(updated);
      // Sync list
      setEntries((prev) =>
        prev.map((e) =>
          e.entry_id === updated.entry_id
            ? {
                ...e,
                title: updated.title,
                mood: updated.mood,
                tags: updated.tags,
              }
            : e,
        ),
      );
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Không thể cập nhật nhật ký";
      setError(msg);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteEntry = async (entryId: number) => {
    if (!confirm(`Xóa entry #${entryId}? Hành động này không thể hoàn tác.`)) return;
    setError(null);
    try {
      await apiClient.deleteJournalEntry(entryId);
      setEntries((prev) => prev.filter((e) => e.entry_id !== entryId));
      if (selectedEntry?.entry_id === entryId) {
        setSelectedEntry(null);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Không thể xóa nhật ký";
      setError(msg);
    }
  };

  return (
    <section className="flex flex-col h-[calc(100vh-120px)] max-w-6xl mx-auto px-4 py-4 gap-4">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h1 className="text-2xl font-bold">Quản lý dữ liệu</h1>
          <p className="text-sm text-muted-foreground">
            Quản lý nhật ký, nội dung và media (CRUD).
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadEntries} disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="size-4 animate-spin mr-2" /> Đang tải...
            </>
          ) : (
            <>
              <RefreshCw className="size-4 mr-2" /> Làm mới
            </>
          )}
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive text-sm rounded-lg p-3">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-[2fr,3fr] gap-4 flex-1 min-h-0">
        {/* Left: list */}
        <div className="border border-border rounded-lg p-3 overflow-y-auto">
          <h2 className="text-sm font-semibold mb-2">Danh sách nhật ký</h2>
          {entries.length === 0 && !isLoading && (
            <p className="text-xs text-muted-foreground">Chưa có entry nào.</p>
          )}
          <div className="space-y-2">
            {entries.map((entry) => (
              <button
                key={entry.entry_id}
                onClick={() => void handleSelectEntry(entry.entry_id)}
                className={`w-full text-left rounded-lg border px-3 py-2 text-sm transition-colors ${
                  selectedEntry?.entry_id === entry.entry_id
                    ? "border-primary bg-primary/10"
                    : "border-border hover:bg-muted/50"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <div className="font-medium truncate">{entry.title}</div>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    {entry.media_count > 0 && (
                      <span className="inline-flex items-center gap-1">
                        <ImageIcon className="size-3" />
                        {entry.media_count}
                      </span>
                    )}
                    <span>
                      {new Date(entry.created_at).toLocaleDateString("vi-VN", {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                      })}
                    </span>
                  </div>
                </div>
                {entry.tags.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {entry.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-[10px] px-1.5 py-0.5 rounded bg-muted text-muted-foreground"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Right: detail/editor */}
        <div className="border border-border rounded-lg p-4 overflow-y-auto">
          {selectedEntry ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between gap-2">
                <h2 className="text-sm font-semibold flex items-center gap-2">
                  <Edit3 className="size-4" />
                  Nhật ký #{selectedEntry.entry_id}
                </h2>
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => void handleDeleteEntry(selectedEntry.entry_id)}
                >
                  <Trash2 className="size-4 mr-1" />
                  Xóa
                </Button>
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium">Tiêu đề</label>
                <input
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background"
                  value={selectedEntry.title}
                  onChange={(e) =>
                    setSelectedEntry((prev) =>
                      prev ? { ...prev, title: e.target.value } : prev,
                    )
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium">Tâm trạng</label>
                <input
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background"
                  value={selectedEntry.mood ?? ""}
                  onChange={(e) =>
                    setSelectedEntry((prev) =>
                      prev ? { ...prev, mood: e.target.value } : prev,
                    )
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium">Thẻ (ngăn cách bằng dấu phẩy)</label>
                <input
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background"
                  value={selectedEntry.tags.join(", ")}
                  onChange={(e) =>
                    setSelectedEntry((prev) =>
                      prev
                        ? {
                            ...prev,
                            tags: e.target.value
                              .split(",")
                              .map((t) => t.trim())
                              .filter(Boolean),
                          }
                        : prev,
                    )
                  }
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-medium">Nội dung</label>
                <textarea
                  className="w-full px-2 py-1.5 text-sm rounded-md border border-input bg-background min-h-[160px] resize-vertical"
                  value={selectedEntry.content}
                  onChange={(e) =>
                    setSelectedEntry((prev) =>
                      prev ? { ...prev, content: e.target.value } : prev,
                    )
                  }
                />
              </div>

              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>
                  Tạo lúc:{" "}
                  {new Date(selectedEntry.created_at).toLocaleString("vi-VN", {
                    dateStyle: "short",
                    timeStyle: "short",
                  })}
                </span>
                <span>
                  Cập nhật:{" "}
                  {new Date(selectedEntry.updated_at).toLocaleString("vi-VN", {
                    dateStyle: "short",
                    timeStyle: "short",
                  })}
                </span>
              </div>

              {selectedEntry.media.length > 0 && (
                <div className="mt-3 border-t border-border pt-3 space-y-2">
                  <p className="text-xs font-semibold flex items-center gap-1">
                    <ImageIcon className="size-3" /> Tệp đính kèm ({selectedEntry.media.length})
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {selectedEntry.media.map((m) => {
                      const href = apiClient.getMediaUrl(m.id);
                      return (
                        <a
                          key={m.id}
                          href={href}
                          target="_blank"
                          rel="noopener noreferrer"
                          download
                          className="text-xs px-2 py-1 rounded bg-primary/10 text-primary border border-primary/20 hover:bg-primary/20 transition-colors"
                        >
                          📎 {m.type} (tải xuống)
                        </a>
                      );
                    })}
                  </div>
                </div>
              )}

              <div className="pt-2">
                <Button onClick={() => void handleUpdateEntry()} disabled={isSaving}>
                  {isSaving ? (
                    <>
                      <Loader2 className="size-4 animate-spin mr-2" />
                      Đang lưu...
                    </>
                  ) : (
                    "Lưu thay đổi"
                  )}
                </Button>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-sm text-muted-foreground">
              Chọn một entry bên trái để xem và chỉnh sửa.
            </div>
          )}
        </div>
      </div>
    </section>
  );
}


