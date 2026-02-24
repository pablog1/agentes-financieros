import Link from "next/link";
import { AgentAvatar } from "../agents/AgentAvatar";
import { formatDateShort } from "@/lib/dates";

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
  variant?: "default" | "hero";
}

export function ReportCard({
  agentId,
  agentName,
  reportName,
  agentColor,
  avatarUrl,
  title,
  excerpt,
  date,
  wordCount,
  variant = "default",
}: ReportCardProps) {
  const dateStr = typeof date === "string" ? date : date.toISOString().split("T")[0];
  const href = `/analista/${agentId}/${dateStr}`;

  if (variant === "hero") {
    return (
      <Link href={href} className="block group">
        <article
          className="bg-card rounded-sm p-6 border-l-4 hover:shadow-lg transition-shadow"
          style={{ borderLeftColor: agentColor }}
        >
          <div className="flex items-center gap-3 mb-4">
            <AgentAvatar name={agentName} color={agentColor} avatarUrl={avatarUrl} size="lg" />
            <div>
              <span className="font-semibold text-lg">{agentName}</span>
              <span className="block text-sm text-muted-foreground">{reportName}</span>
            </div>
          </div>
          <h2
            className="text-2xl md:text-3xl font-bold mb-3 group-hover:text-accent transition-colors leading-tight"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            {title}
          </h2>
          <p className="text-muted-foreground leading-relaxed mb-4 text-base">
            {excerpt}
          </p>
          <div className="flex items-center gap-3 text-xs text-muted-foreground">
            <time>{formatDateShort(dateStr)}</time>
            <span>&middot;</span>
            <span>{wordCount} palabras</span>
            <span>&middot;</span>
            <span className="group-hover:text-accent transition-colors">Leer completo →</span>
          </div>
        </article>
      </Link>
    );
  }

  return (
    <Link href={href} className="block group">
      <article
        className="bg-card rounded-sm p-4 border-l-3 hover:shadow-md transition-shadow h-full flex flex-col"
        style={{ borderLeftColor: agentColor }}
      >
        <div className="flex items-center gap-2 mb-3">
          <AgentAvatar name={agentName} color={agentColor} avatarUrl={avatarUrl} size="sm" />
          <div className="leading-tight">
            <span className="text-sm font-medium">{agentName}</span>
            <span className="block text-xs text-muted-foreground">{reportName}</span>
          </div>
        </div>
        <h3
          className="text-lg font-semibold mb-2 group-hover:text-accent transition-colors leading-snug"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          {title}
        </h3>
        <p className="text-sm text-muted-foreground leading-relaxed mb-3 flex-1 line-clamp-3">
          {excerpt}
        </p>
        <div className="flex items-center gap-2 text-xs text-muted-foreground mt-auto">
          <time>{formatDateShort(dateStr)}</time>
          <span>&middot;</span>
          <span>{wordCount} pal.</span>
        </div>
      </article>
    </Link>
  );
}
