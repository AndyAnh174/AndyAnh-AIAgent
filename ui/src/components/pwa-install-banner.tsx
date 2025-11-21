"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Sparkles, X, Wifi } from "lucide-react";
import { cn } from "@/lib/utils";

declare global {
  interface BeforeInstallPromptEvent extends Event {
    readonly platforms: string[];
    prompt: () => Promise<void>;
    userChoice: Promise<{ outcome: "accepted" | "dismissed"; platform: string | undefined }>;
  }

  interface WindowEventMap {
    beforeinstallprompt: BeforeInstallPromptEvent;
  }
}

export function PWAInstallBanner() {
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [visible, setVisible] = useState(false);
  const [status, setStatus] = useState<string>("");

  useEffect(() => {
    if (typeof window === "undefined") return;
    if ("serviceWorker" in navigator && process.env.NODE_ENV === "production") {
      navigator.serviceWorker
        .register("/sw.js")
        .then(() => setStatus("Đang bảo vệ ở chế độ offline"))
        .catch(() => setStatus("Không thể kích hoạt chế độ offline"));
    }

    const hasDismissed = localStorage.getItem("pwa-install-dismissed");
    if (hasDismissed) {
      return;
    }

    const handler = (event: BeforeInstallPromptEvent) => {
      event.preventDefault();
      setDeferredPrompt(event);
      setVisible(true);
    };

    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    await deferredPrompt.prompt();
    const choice = await deferredPrompt.userChoice;
    if (choice.outcome === "accepted") {
      setStatus("Đã cài đặt trên thiết bị của bạn");
      setVisible(false);
    } else {
      setStatus("Bạn có thể cài đặt sau tại menu trình duyệt");
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    localStorage.setItem("pwa-install-dismissed", "true");
    setVisible(false);
  };

  if (!visible && !status) {
    return null;
  }

  return (
    <div className="fixed bottom-4 inset-x-4 z-40 md:bottom-6 md:left-auto md:right-10 md:w-96">
      <div
        className={cn(
          "relative overflow-hidden rounded-3xl border border-white/10 bg-background/90 shadow-2xl backdrop-blur",
          "before:absolute before:inset-0 before:bg-[radial-gradient(circle_at_top,#a855f7_0%,transparent_60%)] before:opacity-40",
        )}
      >
        <div className="relative p-4 space-y-2">
          <div className="flex items-start gap-3">
            <div className="flex size-10 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-pink-500 text-white shadow-lg">
              <Sparkles className="size-4" />
            </div>
            <div className="flex-1">
              <p className="text-sm font-semibold">Cài đặt AI Life Companion</p>
              <p className="text-xs text-muted-foreground">
                Truy cập như một app độc lập, có offline mode và sync thông minh.
              </p>
            </div>
            <button
              type="button"
              aria-label="Đóng banner"
              className="text-muted-foreground hover:text-foreground transition"
              onClick={handleDismiss}
            >
              <X className="size-4" />
            </button>
          </div>
          {status && (
            <div className="flex items-center gap-2 text-xs text-indigo-200">
              <Wifi className="size-3" />
              <span>{status}</span>
            </div>
          )}
          {visible && (
            <div className="flex gap-2 pt-2">
              <Button className="flex-1" onClick={handleInstall}>
                Cài đặt ngay
              </Button>
              <Button variant="outline" onClick={handleDismiss}>
                Để sau
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

