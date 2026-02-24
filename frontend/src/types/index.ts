export type { Agent, Report, DailyData } from "@/generated/prisma/client";

export interface ReportWithAgent {
  id: number;
  agentId: string;
  date: Date;
  title: string;
  content: string;
  wordCount: number;
  excerpt: string;
  createdAt: Date;
  updatedAt: Date;
  agent: {
    id: string;
    name: string;
    fullAlias: string;
    reportName: string;
    color: string;
    avatarUrl: string | null;
    sortOrder: number;
    motto: string;
  };
}

export interface DateEntry {
  date: string;
  reportCount: number;
}
