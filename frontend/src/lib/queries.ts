import { prisma } from "./db";

export async function getAgents() {
  return prisma.agent.findMany({
    orderBy: { sortOrder: "asc" },
  });
}

export async function getAgent(id: string) {
  return prisma.agent.findUnique({ where: { id } });
}

export async function getLatestReports() {
  const latestDate = await prisma.report.findFirst({
    orderBy: { date: "desc" },
    select: { date: true },
  });

  if (!latestDate) return [];

  return prisma.report.findMany({
    where: { date: latestDate.date },
    include: { agent: true },
    orderBy: { agent: { sortOrder: "asc" } },
  });
}

export async function getReportsByDate(date: Date) {
  return prisma.report.findMany({
    where: { date },
    include: { agent: true },
    orderBy: { agent: { sortOrder: "asc" } },
  });
}

export async function getReport(agentId: string, date: Date) {
  return prisma.report.findUnique({
    where: { agentId_date: { agentId, date } },
    include: { agent: true },
  });
}

export async function getReportsByAgent(agentId: string, limit = 30) {
  return prisma.report.findMany({
    where: { agentId },
    include: { agent: true },
    orderBy: { date: "desc" },
    take: limit,
  });
}

export async function getAvailableDates(limit = 60) {
  const dates = await prisma.report.findMany({
    select: { date: true },
    distinct: ["date"],
    orderBy: { date: "desc" },
    take: limit,
  });

  // Count reports per date
  const result = await Promise.all(
    dates.map(async ({ date }) => {
      const count = await prisma.report.count({ where: { date } });
      return { date: date.toISOString().split("T")[0], reportCount: count };
    })
  );

  return result;
}

export async function getLatestDate(): Promise<string | null> {
  const latest = await prisma.report.findFirst({
    orderBy: { date: "desc" },
    select: { date: true },
  });
  return latest ? latest.date.toISOString().split("T")[0] : null;
}
