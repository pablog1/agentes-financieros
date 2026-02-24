import { AgentAvatar } from "./AgentAvatar";
import type { Agent } from "@/types";

interface AgentProfileProps {
  agent: Agent;
}

export function AgentProfile({ agent }: AgentProfileProps) {
  return (
    <div className="flex flex-col sm:flex-row items-start gap-6 mb-8 pb-8 border-b border-border">
      <AgentAvatar
        name={agent.name}
        color={agent.color}
        avatarUrl={agent.avatarUrl}
        size="lg"
      />
      <div className="flex-1">
        <h1
          className="text-2xl md:text-3xl font-bold mb-1"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          {agent.name}
        </h1>
        <p className="text-muted-foreground mb-3">{agent.fullAlias}</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-muted-foreground">Reporte:</span>{" "}
            <span className="font-medium">{agent.reportName}</span>
          </div>
          <div>
            <span className="text-muted-foreground">Edad:</span>{" "}
            <span className="font-medium">{agent.age} años</span>
          </div>
          <div className="sm:col-span-2">
            <span className="text-muted-foreground">Perfil de riesgo:</span>{" "}
            <span className="font-medium">{agent.riskStance}</span>
          </div>
          <div className="sm:col-span-2">
            <span className="text-muted-foreground">Audiencia:</span>{" "}
            <span className="font-medium">{agent.audience}</span>
          </div>
          <div className="sm:col-span-2">
            <span className="text-muted-foreground">Personalidad:</span>{" "}
            <span>{agent.personality}</span>
          </div>
        </div>

        <p className="text-sm italic text-muted-foreground mt-4 pt-3 border-t border-border">
          &ldquo;{agent.motto}&rdquo;
        </p>
      </div>
    </div>
  );
}
