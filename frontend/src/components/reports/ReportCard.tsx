import Link from "next/link";
import { formatDateShort } from "@/lib/dates";
import { AGENT_SECTIONS } from "@/lib/agents";

interface ReportCardProps {
  agentId: string;
  agentName: string;
  reportName: string;
  agentColor: string;
  avatarUrl?: string | null;
  title: string;
  excerpt: string;
  date: Date | string;
  wordCount: number;
  variant?: "lead" | "secondary" | "column";
}

export function ReportCard({
  agentId,
  agentName,
  reportName,
  agentColor,
  title,
  excerpt,
  date,
  wordCount,
  variant = "column",
}: ReportCardProps) {
  const dateStr = typeof date === "string" ? date : date.toISOString().split("T")[0];
  const href = `/analista/${agentId}/${dateStr}`;
  const section = AGENT_SECTIONS[agentId];

  if (variant === "lead") {
    return (
      <Link href={href} className="block group">
        <article>
          <h2 className="headline-lead mb-3 group-hover:text-accent transition-colors">
            {title}
          </h2>
          <div className="byline mb-3 flex items-center gap-2">
            <span style={{ color: agentColor }}>&#9679;</span>
            <span>{section ? `${section} (${agentName})` : agentName}</span>
            <span>&middot;</span>
            <time>{formatDateShort(dateStr)}</time>
          </div>
          <p className="excerpt-text mb-4">
            {excerpt}
          </p>
          <span className="text-sm font-medium text-accent group-hover:underline">
            Leer completo &rarr;
          </span>
        </article>
      </Link>
    );
  }

  if (variant === "secondary") {
    return (
      <Link href={href} className="block group sidebar-item">
        <article>
          <h3 className="headline-secondary mb-2 group-hover:text-accent transition-colors">
            {title}
          </h3>
          <div className="byline mb-2 flex items-center gap-1.5">
            <span style={{ color: agentColor }}>&#9679;</span>
            <span>{section ? `${section} (${agentName})` : agentName}</span>
            <span>&middot;</span>
            <time>{formatDateShort(dateStr)}</time>
          </div>
          <p className="text-sm leading-relaxed line-clamp-5" style={{ fontFamily: "var(--font-serif)" }}>
            {excerpt}
          </p>
          <span className="text-sm font-medium text-accent group-hover:underline mt-2 inline-block">
            Leer completo &rarr;
          </span>
        </article>
      </Link>
    );
  }

  // column (default)
  return (
    <Link href={href} className="block group">
      <article>
        <h3 className="headline-tertiary mb-2 group-hover:text-accent transition-colors">
          {title}
        </h3>
        <div className="byline mb-2 flex items-center gap-1.5">
          <span style={{ color: agentColor }}>&#9679;</span>
          <span>{agentName}</span>
          <span>&middot;</span>
          <time>{formatDateShort(dateStr)}</time>
        </div>
        <p className="text-sm leading-relaxed line-clamp-4" style={{ fontFamily: "var(--font-serif)" }}>
          {excerpt}
        </p>
        <span className="text-sm font-medium text-accent group-hover:underline mt-2 inline-block">
          Leer completo &rarr;
        </span>
      </article>
    </Link>
  );
}
