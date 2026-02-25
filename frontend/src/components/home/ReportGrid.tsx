import Link from "next/link";
import type { ReactNode } from "react";
import { ReportCard } from "../reports/ReportCard";
import type { ReportWithAgent } from "@/types";
import { formatDateShort } from "@/lib/dates";
import { AGENT_SECTIONS } from "@/lib/agents";

/** Parse inline **bold** markdown into React nodes */
function parseInlineBold(text: string): ReactNode[] {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return parts.map((part, i) =>
    i % 2 === 1 ? <strong key={i}>{part}</strong> : part
  );
}

interface ReportGridProps {
  reports: ReportWithAgent[];
}

/**
 * Extract the first N paragraphs of markdown content (after title lines).
 * Strips H1/H2 headers and returns plain-ish text for inline display.
 */
function extractLeadContent(content: string, maxParagraphs = 4): string {
  const lines = content.split("\n");
  const paragraphs: string[] = [];
  let currentPara = "";
  let pastTitle = false;

  for (const line of lines) {
    const trimmed = line.trim();
    // Skip the H1 title and the bold subtitle line
    if (!pastTitle) {
      if (trimmed.startsWith("# ") || trimmed.startsWith("**")) {
        continue;
      }
      if (trimmed.startsWith("## ")) {
        pastTitle = true;
        continue;
      }
      if (trimmed === "") continue;
      pastTitle = true;
    }

    // Skip section headers
    if (trimmed.startsWith("## ") || trimmed.startsWith("### ")) {
      if (currentPara) {
        paragraphs.push(currentPara.trim());
        currentPara = "";
      }
      if (paragraphs.length >= maxParagraphs) break;
      continue;
    }

    // Skip blockquotes (disclaimers)
    if (trimmed.startsWith("> ")) continue;

    if (trimmed === "") {
      if (currentPara) {
        paragraphs.push(currentPara.trim());
        currentPara = "";
        if (paragraphs.length >= maxParagraphs) break;
      }
    } else {
      currentPara += (currentPara ? " " : "") + trimmed;
    }
  }
  if (currentPara && paragraphs.length < maxParagraphs) {
    paragraphs.push(currentPara.trim());
  }

  return paragraphs.join("\n\n");
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

  // Find the editor report (lead/editorial) and separate from the rest
  const editorReport = reports.find((r) => r.agentId === "editor");
  const otherReports = reports.filter((r) => r.agentId !== "editor");

  // First analyst report for sidebar lead, rest for columns
  const sidebarReports = otherReports.slice(0, 3);
  const columnReports = otherReports.slice(3);

  return (
    <div>
      {/* Lead editorial + sidebar analysts */}
      <div className="flex flex-col lg:grid lg:gap-6" style={{ gridTemplateColumns: "3fr 2fr" }}>
        {/* Main editorial */}
        {editorReport ? (
          <div>
            <LeadEditorial report={editorReport} />
          </div>
        ) : otherReports[0] ? (
          <div>
            <ReportCard
              agentId={otherReports[0].agentId}
              agentName={otherReports[0].agent.name}
              reportName={otherReports[0].agent.reportName}
              agentColor={otherReports[0].agent.color}
              title={otherReports[0].title}
              excerpt={otherReports[0].excerpt}
              date={otherReports[0].date}
              wordCount={otherReports[0].wordCount}
              variant="lead"
            />
          </div>
        ) : null}

        {/* Sidebar */}
        {sidebarReports.length > 0 && (
          <div className="mt-4 pt-4 border-t border-border lg:mt-0 lg:pt-0 lg:border-t-0 lg:border-l lg:pl-5">
            {sidebarReports.map((report) => (
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

      {/* Column stories */}
      {columnReports.length > 0 && (
        <>
          <hr
            className="my-6"
            style={{ border: "none", borderTop: "3px double var(--foreground)" }}
          />

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4">
            {columnReports.map((report, i) => (
              <div
                key={report.id}
                className={`py-3 md:py-0 ${
                  i > 0 ? "border-t border-border md:border-t-0 md:border-l md:pl-4" : ""
                }`}
                style={{ paddingRight: i < columnReports.length - 1 ? "1rem" : 0 }}
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

/**
 * Lead editorial component — shows the editor's report with substantial content inline.
 */
function LeadEditorial({ report }: { report: ReportWithAgent }) {
  const dateStr = typeof report.date === "string" ? report.date : report.date.toISOString().split("T")[0];
  const href = `/analista/${report.agentId}/${dateStr}`;
  const leadContent = extractLeadContent(report.content, 2);

  return (
    <article>
      <Link href={href} className="block group">
        <h2 className="headline-lead mb-2 group-hover:text-accent transition-colors">
          {report.title}
        </h2>
      </Link>
      <div className="byline mb-3 flex items-center gap-2">
        <span style={{ color: report.agent.color }}>&#9679;</span>
        <span>{AGENT_SECTIONS[report.agentId] ? `${AGENT_SECTIONS[report.agentId]} (${report.agent.name})` : `Por ${report.agent.name}`}</span>
        <span>&middot;</span>
        <time>{formatDateShort(dateStr)}</time>
      </div>
      <div className="lead-content mb-3" style={{ fontFamily: "var(--font-serif)", lineHeight: 1.65, fontSize: "1.02rem" }}>
        {leadContent.split("\n\n").map((para, i) => (
          <p key={i} className="mb-2.5">
            {parseInlineBold(para)}
          </p>
        ))}
      </div>
      <Link
        href={href}
        className="text-sm font-medium text-accent hover:underline"
      >
        Leer completo &rarr;
      </Link>
    </article>
  );
}
