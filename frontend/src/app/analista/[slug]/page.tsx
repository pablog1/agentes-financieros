import { notFound } from "next/navigation";
import { getAgent, getReportsByAgent } from "@/lib/queries";
import { AgentProfile } from "@/components/agents/AgentProfile";
import { ReportCard } from "@/components/reports/ReportCard";
import type { Metadata } from "next";
import type { ReportWithAgent } from "@/types";

interface PageProps {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { slug } = await params;
  const agent = await getAgent(slug);

  if (!agent) return { title: "Analista no encontrado" };

  return {
    title: `${agent.name} — ${agent.reportName} — El Periódico Financiero`,
    description: `${agent.fullAlias}. ${agent.personality}`,
  };
}

export default async function AgentPage({ params }: PageProps) {
  const { slug } = await params;
  const agent = await getAgent(slug);

  if (!agent) notFound();

  const reports = (await getReportsByAgent(slug)) as ReportWithAgent[];

  return (
    <div>
      <AgentProfile agent={agent} />

      <h2
        className="text-xl font-semibold mb-6"
        style={{ fontFamily: "var(--font-serif)" }}
      >
        Reportes recientes
      </h2>

      {reports.length === 0 ? (
        <p className="text-muted-foreground text-center py-8">
          Aún no hay reportes de {agent.name}.
        </p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {reports.map((report) => (
            <ReportCard
              key={report.id}
              agentId={report.agentId}
              agentName={report.agent.name}
              reportName={report.agent.reportName}
              agentColor={report.agent.color}
              avatarUrl={report.agent.avatarUrl}
              title={report.title}
              excerpt={report.excerpt}
              date={report.date}
              wordCount={report.wordCount}
            />
          ))}
        </div>
      )}
    </div>
  );
}
