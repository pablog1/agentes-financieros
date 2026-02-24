import { NextRequest, NextResponse } from "next/server";
import { prisma } from "@/lib/db";

function checkSecret(req: NextRequest): boolean {
  const secret = req.headers.get("x-api-secret");
  return secret === process.env.API_SECRET;
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const date = searchParams.get("date");
  const agent = searchParams.get("agent");
  const limit = parseInt(searchParams.get("limit") || "30");

  const where: Record<string, unknown> = {};
  if (date) where.date = new Date(date + "T00:00:00.000Z");
  if (agent) where.agentId = agent;

  const reports = await prisma.report.findMany({
    where,
    include: { agent: true },
    orderBy: [{ date: "desc" }, { agent: { sortOrder: "asc" } }],
    take: Math.min(limit, 100),
  });

  return NextResponse.json(reports);
}

export async function POST(req: NextRequest) {
  if (!checkSecret(req)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const body = await req.json();
  const { agent_id, date, title, content, word_count, excerpt } = body;

  if (!agent_id || !date || !content) {
    return NextResponse.json(
      { error: "Missing required fields: agent_id, date, content" },
      { status: 400 }
    );
  }

  const report = await prisma.report.upsert({
    where: { agentId_date: { agentId: agent_id, date: new Date(date + "T00:00:00.000Z") } },
    update: { title, content, wordCount: word_count, excerpt, updatedAt: new Date() },
    create: {
      agentId: agent_id,
      date: new Date(date + "T00:00:00.000Z"),
      title,
      content,
      wordCount: word_count,
      excerpt,
    },
  });

  return NextResponse.json(report, { status: 201 });
}
