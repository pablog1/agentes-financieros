import { AgentBadge } from "../agents/AgentBadge";
import { MarkdownRenderer } from "./MarkdownRenderer";
import { formatDateLong } from "@/lib/dates";
import Link from "next/link";

interface ReportFullProps {
  agentId: string;
  agentName: string;
  agentAlias: string;
  reportName: string;
  agentColor: string;
  avatarUrl?: string | null;
  motto: string;
  title: string;
  content: string;
  date: Date | string;
  wordCount: number;
}

export function ReportFull({
  agentId,
  agentName,
  agentAlias,
  reportName,
  agentColor,
  avatarUrl,
  motto,
  title,
  content,
  date,
  wordCount,
}: ReportFullProps) {
  const dateStr = typeof date === "string" ? date : date.toISOString().split("T")[0];

  // Remove the H1 title from content since we render it separately
  const bodyContent = content.replace(/^#\s+.+$/m, "").trim();

  return (
    <article className="max-w-3xl mx-auto">
      {/* Breadcrumb */}
      <nav className="text-sm text-muted-foreground mb-6 flex items-center gap-1.5">
        <Link href="/" className="hover:text-accent transition-colors">Inicio</Link>
        <span>/</span>
        <Link href={`/analista/${agentId}`} className="hover:text-accent transition-colors">{agentName}</Link>
        <span>/</span>
        <span>{formatDateLong(dateStr)}</span>
      </nav>

      {/* Header */}
      <header className="mb-8">
        <div className="flex items-center gap-3 mb-4">
          <AgentBadge
            id={agentId}
            name={agentName}
            reportName={reportName}
            color={agentColor}
            avatarUrl={avatarUrl}
          />
        </div>

        <h1
          className="text-3xl md:text-4xl font-bold leading-tight mb-3"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          {title}
        </h1>

        <div className="flex items-center gap-3 text-sm text-muted-foreground pb-4 border-b border-border">
          <time>{formatDateLong(dateStr)}</time>
          <span>&middot;</span>
          <span>{wordCount} palabras</span>
        </div>
      </header>

      {/* Report body */}
      <div
        className="border-l-4 pl-6 md:pl-8"
        style={{ borderLeftColor: agentColor }}
      >
        <MarkdownRenderer content={bodyContent} />
      </div>

      {/* Motto / Disclaimer */}
      <footer className="mt-8 pt-6 border-t border-border text-center">
        <p className="text-sm italic text-muted-foreground">{motto}</p>
        <p className="text-xs text-muted-foreground mt-2">
          — {agentAlias}
        </p>
      </footer>
    </article>
  );
}
