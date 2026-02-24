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

  // Lead story (first report, typically Manu)
  const lead = reports[0];
  // Sidebar stories (2nd and 3rd, typically Tomi and Vale)
  const sidebar = reports.slice(1, 3);
  // Column stories (rest)
  const columns = reports.slice(3);

  return (
    <div>
      {/* Lead + Sidebar — 2fr 1fr on desktop, stacked on mobile */}
      <div className="flex flex-col lg:grid lg:gap-8" style={{ gridTemplateColumns: "2fr 1fr" }}>
        {/* Main story */}
        <div>
          <ReportCard
            agentId={lead.agentId}
            agentName={lead.agent.name}
            reportName={lead.agent.reportName}
            agentColor={lead.agent.color}
            title={lead.title}
            excerpt={lead.excerpt}
            date={lead.date}
            wordCount={lead.wordCount}
            variant="lead"
          />
        </div>

        {/* Sidebar */}
        {sidebar.length > 0 && (
          <div className="mt-6 pt-6 border-t border-border lg:mt-0 lg:pt-0 lg:border-t-0 lg:border-l lg:pl-6">
            {sidebar.map((report) => (
              <ReportCard
                key={report.id}
                agentId={report.agentId}
                agentName={report.agent.name}
                reportName={report.agent.reportName}
                agentColor={report.agent.color}
                title={report.title}
                excerpt={report.excerpt}
                date={report.date}
                wordCount={report.wordCount}
                variant="secondary"
              />
            ))}
          </div>
        )}
      </div>

      {/* Heavy rule separator */}
      {columns.length > 0 && (
        <>
          <hr
            className="my-8"
            style={{ border: "none", borderTop: "3px double var(--foreground)" }}
          />

          {/* Column stories — 4 cols desktop, 2 cols tablet, 1 col mobile */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
            {columns.map((report, i) => (
              <div
                key={report.id}
                className={`py-4 md:py-0 ${
                  i > 0 ? "border-t border-border md:border-t-0 md:border-l md:pl-5" : ""
                }`}
                style={{ paddingRight: i < columns.length - 1 ? "1.25rem" : 0 }}
              >
                <ReportCard
                  agentId={report.agentId}
                  agentName={report.agent.name}
                  reportName={report.agent.reportName}
                  agentColor={report.agent.color}
                  title={report.title}
                  excerpt={report.excerpt}
                  date={report.date}
                  wordCount={report.wordCount}
                  variant="column"
                />
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
