import Link from "next/link";
import { AgentAvatar } from "./AgentAvatar";

interface AgentBadgeProps {
  id: string;
  name: string;
  reportName: string;
  color: string;
  avatarUrl?: string | null;
}

export function AgentBadge({ id, name, reportName, color, avatarUrl }: AgentBadgeProps) {
  return (
    <Link
      href={`/analista/${id}`}
      className="flex items-center gap-2 group"
    >
      <AgentAvatar name={name} color={color} avatarUrl={avatarUrl} size="sm" />
      <div className="leading-tight">
        <span className="text-sm font-medium group-hover:text-accent transition-colors">
          {name}
        </span>
        <span className="block text-xs text-muted-foreground">{reportName}</span>
      </div>
    </Link>
  );
}
