"use client";

import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";
import { BookOpen, Search, Bell, Plus } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

export function DashboardSection() {
  const [isConnected, setIsConnected] = useState(false);
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    const checkConnection = async () => {
      try {
        await apiClient.healthCheck();
        setIsConnected(true);
      } catch (error) {
        setIsConnected(false);
      } finally {
        setIsChecking(false);
      }
    };

    checkConnection();
  }, []);

  const features = [
    {
      icon: BookOpen,
      title: "Nhật ký",
      description: "Viết và quản lý nhật ký bằng văn bản, hình ảnh, PDF hoặc video",
      href: "/journal",
      color: "text-blue-500",
    },
    {
      icon: Search,
      title: "Truy vấn AI",
      description: "Hỏi lại ký ức bằng ngôn ngữ tự nhiên thông qua GraphRAG",
      href: "/query",
      color: "text-purple-500",
    },
    {
      icon: Bell,
      title: "Nhắc nhở",
      description: "Tạo nhắc nhở chủ động cho những sự kiện quan trọng",
      href: "/reminders",
      color: "text-orange-500",
    },
  ];

  return (
    <section className="w-full max-w-7xl mx-auto px-4 py-12 md:py-24">
      <div className="flex flex-col items-center text-center space-y-8">
        <div className="space-y-4">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
            AI Life Companion
          </h1>
          <p className="text-xl text-muted-foreground max-w-2xl">
            Nhật ký thông minh và bản sao số của bạn được vận hành bởi AI. Ghi lại ký ức, truy vấn quá khứ và nhận nhắc nhở chủ động.
          </p>
        </div>

        <div className="flex items-center gap-2 text-sm">
          <div
            className={`size-2 rounded-full ${
              isChecking
                ? "bg-yellow-500 animate-pulse"
                : isConnected
                  ? "bg-green-500"
                  : "bg-red-500"
            }`}
          />
          <span className="text-muted-foreground">
            {isChecking
              ? "Đang kiểm tra kết nối..."
              : isConnected
                ? "Đã kết nối tới API"
                : "Không thể kết nối API"}
          </span>
        </div>

        {!isConnected && (
          <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-4 max-w-md">
            <p className="text-sm text-yellow-600 dark:text-yellow-400">
              Vui lòng cấu hình API key tại{" "}
              <Link href="/settings" className="underline font-medium">
                Cài đặt
              </Link>{" "}
              và chắc chắn rằng backend đang hoạt động.
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 w-full mt-12">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link
                key={feature.href}
                href={feature.href}
                className="group relative p-6 rounded-lg border border-border bg-card hover:border-primary/50 transition-all hover:shadow-lg"
              >
                <div className="flex flex-col space-y-4">
                  <div className={`${feature.color} group-hover:scale-110 transition-transform`}>
                    <Icon className="size-8" />
                  </div>
                  <div className="space-y-2">
                    <h3 className="text-xl font-semibold">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {feature.description}
                    </p>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>

        <div className="flex gap-4 mt-8">
          <Button asChild size="lg">
            <Link href="/journal">
              <Plus className="size-4 mr-2" />
              Tạo nhật ký mới
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/query">Trải nghiệm truy vấn</Link>
          </Button>
        </div>
      </div>
    </section>
  );
}
