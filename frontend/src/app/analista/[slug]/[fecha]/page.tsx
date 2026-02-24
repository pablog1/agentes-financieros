import { notFound } from "next/navigation";
import { getReport } from "@/lib/queries";
import { ReportFull } from "@/components/reports/ReportFull";
import type { Metadata } from "next";

interface PageProps {
  params: Promise<{ slug: string; fecha: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug, fecha } = await params;
  const report = await getReport(slug, new Date(fecha + "T00:00:00.000Z"));

  if (!report) return { title: "Reporte no encontrado" };

  return {
    title: `${report.title} — El Periódico Financiero`,
    description: report.excerpt,
  };
}

export default async function ReportPage({ params }: PageProps) {
  const { slug, fecha } = await params;
  const report = await getReport(slug, new Date(fecha + "T00:00:00.000Z"));

  if (!report) notFound();

  return (
    <ReportFull
      agentId={report.agent.id}
      agentName={report.agent.name}
      agentAlias={report.agent.fullAlias}
      reportName={report.agent.reportName}
      agentColor={report.agent.color}
      avatarUrl={report.agent.avatarUrl}
      motto={report.agent.motto}
      title={report.title}
      content={report.content}
      date={report.date}
      wordCount={report.wordCount}
    />
  );
}
