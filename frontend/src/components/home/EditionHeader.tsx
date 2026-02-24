import { formatDateFull } from "@/lib/dates";

interface EditionHeaderProps {
  date: string;
  reportCount: number;
}

export function EditionHeader({ date, reportCount }: EditionHeaderProps) {
  return (
    <div className="text-center mb-8">
      <div className="rule-double mb-4" />
      <h2
        className="text-2xl md:text-3xl font-bold mb-1"
        style={{ fontFamily: "var(--font-serif)" }}
      >
        Edición del día
      </h2>
      <p className="text-muted-foreground">
        {formatDateFull(date)} &middot; {reportCount} reportes
      </p>
      <div className="rule-bottom mt-4" />
    </div>
  );
}
