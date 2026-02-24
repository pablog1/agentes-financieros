interface AgentAvatarProps {
  name: string;
  color: string;
  avatarUrl?: string | null;
  size?: "sm" | "md" | "lg";
}

const sizeClasses = {
  sm: "w-8 h-8 text-xs",
  md: "w-10 h-10 text-sm",
  lg: "w-14 h-14 text-lg",
};

export function AgentAvatar({ name, color, avatarUrl, size = "md" }: AgentAvatarProps) {
  const initial = name.charAt(0).toUpperCase();

  if (avatarUrl) {
    return (
      <img
        src={avatarUrl}
        alt={name}
        className={`${sizeClasses[size]} rounded-full object-cover`}
        style={{ outline: `2px solid ${color}`, outlineOffset: "2px" }}
      />
    );
  }

  return (
    <div
      className={`${sizeClasses[size]} rounded-full flex items-center justify-center font-bold text-white`}
      style={{ backgroundColor: color, outline: `2px solid ${color}`, outlineOffset: "2px" }}
    >
      {initial}
    </div>
  );
}
