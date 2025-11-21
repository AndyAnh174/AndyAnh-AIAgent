"use client";

import { useEffect, useState } from "react";
import { apiClient } from "@/lib/api";
import { Loader2, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type MoodTrendPoint = {
  date: string;
  mood: string;
  score: number | null;
};

type TopicStat = {
  topic: string;
  count: number;
};

type AnalysisSummary = {
  mood_trend: MoodTrendPoint[];
  mood_frequency: Record<string, number>;
  top_topics: TopicStat[];
  insights: Array<{ title: string; description: string }>;
  last_updated: string;
};

export function AnalysisSection() {
  const [summary, setSummary] = useState<AnalysisSummary | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiClient.getAnalysisSummary();
      setSummary(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Không thể tải dữ liệu phân tích";
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadSummary();
  }, []);

  return (
    <section className="w-full max-w-6xl mx-auto px-4 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Phân tích con người</h1>
          <p className="text-muted-foreground mt-2">
            Theo dõi tâm trạng, chủ đề nổi bật và insight của Hồ Việt Anh.
          </p>
        </div>
        <Button variant="outline" onClick={() => void loadSummary()} disabled={isLoading}>
          {isLoading ? (
            <>
              <Loader2 className="size-4 animate-spin mr-2" />
              Đang tải...
            </>
          ) : (
            <>
              <RefreshCw className="size-4 mr-2" />
              Làm mới
            </>
          )}
        </Button>
      </div>

      {error && (
        <div className="rounded-xl border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      {!error && !summary && (
        <div className="flex items-center justify-center py-16 text-muted-foreground">
          <Loader2 className="size-5 animate-spin mr-3" />
          Đang phân tích...
        </div>
      )}

      {summary && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <MoodTrendCard trend={summary.mood_trend} />
            <MoodFrequencyCard frequency={summary.mood_frequency} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <TopicCard topics={summary.top_topics} />
            <InsightsCard insights={summary.insights} lastUpdated={summary.last_updated} />
          </div>
        </div>
      )}
    </section>
  );
}

function MoodTrendCard({ trend }: { trend: MoodTrendPoint[] }) {
  return (
    <div className="rounded-xl border border-border/60 bg-background shadow-sm">
      <div className="border-b border-border/60 px-4 py-3">
        <h3 className="text-sm font-semibold">Xu hướng tâm trạng</h3>
      </div>
      <div className="p-4">
        {trend.length === 0 ? (
          <p className="text-muted-foreground text-sm">Chưa có dữ liệu mood.</p>
        ) : (
          <div className="space-y-2">
            {trend.slice(-10).map((point) => (
              <div key={point.date} className="flex items-center justify-between text-sm">
                <span>{new Date(point.date).toLocaleDateString("vi-VN")}</span>
                <span className="font-medium">{point.mood}</span>
                <span className="text-muted-foreground">
                  {point.score !== null ? point.score.toFixed(2) : "n/a"}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MoodFrequencyCard({ frequency }: { frequency: Record<string, number> }) {
  const entries = Object.entries(frequency);
  return (
    <div className="rounded-xl border border-border/60 bg-background shadow-sm">
      <div className="border-b border-border/60 px-4 py-3">
        <h3 className="text-sm font-semibold">Tần suất cảm xúc</h3>
      </div>
      <div className="p-4 space-y-3">
        {entries.length === 0 ? (
          <p className="text-muted-foreground text-sm">Chưa có dữ liệu.</p>
        ) : (
          entries.map(([mood, count]) => (
            <div key={mood} className="space-y-1">
              <div className="flex justify-between text-sm">
                <span>{mood}</span>
                <span className="text-muted-foreground">{count} lần</span>
              </div>
              <div className="h-2 rounded-md bg-muted overflow-hidden">
                <div
                  className={cn("h-full bg-primary")}
                  style={{
                    width: `${Math.min(100, count * 10)}%`,
                  }}
                />
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function TopicCard({ topics }: { topics: TopicStat[] }) {
  return (
    <div className="rounded-xl border border-border/60 bg-background shadow-sm">
      <div className="border-b border-border/60 px-4 py-3">
        <h3 className="text-sm font-semibold">Chủ đề nổi bật</h3>
      </div>
      <div className="p-4">
        {topics.length === 0 ? (
          <p className="text-muted-foreground text-sm">Chưa có chủ đề nổi bật.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {topics.map((topic) => (
              <span
                key={topic.topic}
                className="px-3 py-1 rounded-full border border-border/60 text-sm bg-muted/50"
              >
                {topic.topic} ({topic.count})
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function InsightsCard({ insights, lastUpdated }: { insights: Array<{ title: string; description: string }>; lastUpdated: string }) {
  return (
    <div className="rounded-xl border border-border/60 bg-background shadow-sm">
      <div className="border-b border-border/60 px-4 py-3">
        <h3 className="text-sm font-semibold">Thẻ insight</h3>
        <p className="text-xs text-muted-foreground mt-1">
          Cập nhật lần cuối: {new Date(lastUpdated).toLocaleString("vi-VN")}
        </p>
      </div>
      <div className="p-4 space-y-3">
        {insights.length === 0 ? (
          <p className="text-muted-foreground text-sm">Chưa có insight nào.</p>
        ) : (
          insights.map((insight, idx) => (
            <div key={idx} className="p-3 rounded-xl bg-muted/60 border border-border/40">
              <p className="text-sm font-semibold">{insight.title}</p>
              <p className="text-sm text-muted-foreground mt-1">{insight.description}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

