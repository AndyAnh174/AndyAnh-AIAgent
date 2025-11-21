"use client";

import { Button } from "@/components/ui/button";
import Link from "next/link";
import { WifiOff } from "lucide-react";

export default function OfflinePage() {
  return (
    <main className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-4 px-4">
      <div className="relative border border-border rounded-3xl p-8 max-w-md w-full bg-background/80 shadow-lg">
        <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-purple-500/10 via-indigo-500/10 to-cyan-500/10 blur-3xl -z-10" />
        <WifiOff className="size-10 mx-auto text-muted-foreground" />
        <h1 className="text-2xl font-semibold mt-4">Bạn đang ngoại tuyến</h1>
        <p className="text-sm text-muted-foreground mt-2">
          Không sao đâu. Các trang đã truy cập gần đây vẫn có thể xem được.
          Khi có mạng trở lại hãy làm mới trang để đồng bộ dữ liệu.
        </p>
        <div className="mt-6 flex flex-col sm:flex-row gap-3 justify-center">
          <Button asChild>
            <Link href="/">Về trang chủ</Link>
          </Button>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Thử lại
          </Button>
        </div>
      </div>
    </main>
  );
}

