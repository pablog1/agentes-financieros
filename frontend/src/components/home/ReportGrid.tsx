import { ReportCard } from "../reports/ReportCard";
import type { ReportWithAgent } from "@/types";

interface ReportGridProps {
  reports: ReportWithAgent[];
}

export function ReportGrid({ reports }: ReportGridProps) {
  if (reports.length === 0) {
    return (
      <div className="text-center py-16 text-muted-foreground">
        <p
          className="text-xl mb-2"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          Sin reportes disponibles
        </p>
        <p className="text-sm">Los reportes se generan diariamente.</p>
      </div>
    );
  }

  // First report (Manu) as hero, rest in grid
  const [hero, ...rest] = reports;

  return (
    <div>
      {/* Hero report — Manu */}
      <div className="mb-8">
        <ReportCard
          agentId={hero.agentId}
          agentName={hero.agent.name}
          reportName={hero.agent.reportName}
          agentColor={hero.agent.color}
          avatarUrl={hero.agent.avatarUrl}
          title={hero.title}
          excerpt={hero.excerpt}
          date={hero.date}
          wordCount={hero.wordCount}
          variant="hero"
        />
      </div>

      {/* Grid of remaining reports */}
      {rest.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {rest.map((report) => (
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
