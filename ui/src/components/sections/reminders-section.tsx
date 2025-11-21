"use client";

import { Button } from "@/components/ui/button";
import { apiClient, type CreateReminderRequest } from "@/lib/api";
import { useState } from "react";
import { Bell, Loader2, Plus } from "lucide-react";

export function RemindersSection() {
  const [email, setEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [cadence, setCadence] = useState<
    "once" | "daily" | "weekly" | "monthly" | "yearly"
  >("yearly");
  const [firstRunAt, setFirstRunAt] = useState("");
  const [entryId, setEntryId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setIsSubmitting(true);

    try {
      const request: CreateReminderRequest = {
        email,
        subject,
        body,
        cadence,
        first_run_at: firstRunAt,
        entry_id: entryId ? Number(entryId) : undefined,
      };

      const response = await apiClient.createReminder(request);
      setSuccess(
        `Tạo nhắc nhở thành công! Lần chạy tiếp theo: ${new Date(response.next_run_at).toLocaleString()}`,
      );
      // Reset form
      setEmail("");
      setSubject("");
      setBody("");
      setCadence("yearly");
      setFirstRunAt("");
      setEntryId("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Không thể tạo nhắc nhở");
    } finally {
      setIsSubmitting(false);
    }
  };

  // Get current date/time in ISO format for the input
  const getCurrentDateTime = () => {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    return now.toISOString().slice(0, 16);
  };

  return (
    <section className="w-full max-w-4xl mx-auto px-4 py-12">
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <Bell className="size-6" />
            Tạo nhắc nhở
          </h1>
          <p className="text-muted-foreground mt-2">
            Thiết lập email nhắc nhở cho những sự kiện, ký ức hoặc nhật ký quan trọng. Bạn có thể gửi một lần hoặc lặp lại theo chu kỳ.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              Địa chỉ email *
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background"
              placeholder="user@example.com"
            />
          </div>
          Process SpawnProcess-1:

Traceback (most recent call last):

  File "/usr/local/lib/python3.11/multiprocessing/process.py", line 314, in _bootstrap

    self.run()

  File "/usr/local/lib/python3.11/multiprocessing/process.py", line 108, in run

    self._target(*self._args, **self._kwargs)

          <div className="space-y-2">
            <label htmlFor="subject" className="text-sm font-medium">
              Tiêu đề *
            </label>
            <input
              id="subject"
              type="text"
              required
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background"
              placeholder="Tiêu đề nhắc nhở"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="body" className="text-sm font-medium">
              Nội dung email *
            </label>
            <textarea
              id="body"
              required
              value={body}
              onChange={(e) => setBody(e.target.value)}
              rows={6}
              className="w-full px-3 py-2 rounded-md border border-input bg-background resize-none"
              placeholder="Nội dung bạn muốn gửi..."
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="cadence" className="text-sm font-medium">
                Chu kỳ gửi
              </label>
              <select
                id="cadence"
                value={cadence}
                onChange={(e) =>
                  setCadence(
                    e.target.value as
                      | "once"
                      | "daily"
                      | "weekly"
                      | "monthly"
                      | "yearly",
                  )
                }
                className="w-full px-3 py-2 rounded-md border border-input bg-background"
              >
                <option value="once">Một lần</option>
                <option value="daily">Hằng ngày</option>
                <option value="weekly">Hằng tuần</option>
                <option value="monthly">Hằng tháng</option>
                <option value="yearly">Hằng năm</option>
              </select>
            </div>

            <div className="space-y-2">
              <label htmlFor="firstRunAt" className="text-sm font-medium">
                Thời điểm bắt đầu (UTC) *
              </label>
              <input
                id="firstRunAt"
                type="datetime-local"
                required
                value={firstRunAt}
                onChange={(e) => setFirstRunAt(e.target.value)}
                min={getCurrentDateTime()}
                className="w-full px-3 py-2 rounded-md border border-input bg-background"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label htmlFor="entryId" className="text-sm font-medium">
              ID nhật ký (không bắt buộc)
            </label>
            <input
              id="entryId"
              type="number"
              value={entryId}
              onChange={(e) => setEntryId(e.target.value)}
              className="w-full px-3 py-2 rounded-md border border-input bg-background"
              placeholder="Liên kết tới một nhật ký cụ thể"
            />
            <p className="text-xs text-muted-foreground">
              Nếu cung cấp, nhắc nhở sẽ gắn với nhật ký tương ứng
            </p>
          </div>

          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <p className="text-sm text-destructive">{error}</p>
            </div>
          )}

          {success && (
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
              <p className="text-sm text-green-600 dark:text-green-400">
                {success}
              </p>
            </div>
          )}

          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? (
              <>
                <Loader2 className="size-4 mr-2 animate-spin" />
                Đang tạo...
              </>
            ) : (
              <>
                <Plus className="size-4 mr-2" />
                Tạo nhắc nhở
              </>
            )}
          </Button>
        </form>

        <div className="mt-8 bg-muted/50 border border-border rounded-lg p-6">
          <h3 className="font-semibold mb-2">Ghi chú về nhắc nhở</h3>
          <ul className="text-sm text-muted-foreground space-y-1 list-disc list-inside">
            <li>
              <strong>Một lần:</strong> Gửi đúng vào thời gian đã chọn
            </li>
            <li>
              <strong>Hằng ngày:</strong> Gửi mỗi ngày vào cùng thời điểm
            </li>
            <li>
              <strong>Hằng tuần:</strong> Gửi mỗi tuần vào cùng ngày/giờ
            </li>
            <li>
              <strong>Hằng tháng:</strong> Gửi mỗi tháng vào cùng ngày/giờ
            </li>
            <li>
              <strong>Hằng năm:</strong> Gửi mỗi năm vào cùng ngày/giờ
            </li>
          </ul>
          <p className="text-xs text-muted-foreground mt-4">
            Lưu ý: Nhắc nhở được xử lý bởi worker nền chạy mỗi 60 giây. Hãy đảm bảo backend đã cấu hình email gửi đi.
          </p>
        </div>
      </div>
    </section>
  );
}
