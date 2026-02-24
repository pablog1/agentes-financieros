import Link from "next/link";
import { getAvailableDates } from "@/lib/queries";
import { formatDateFull } from "@/lib/dates";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Archivo — El Periódico Financiero",
  description: "Archivo histórico de reportes financieros diarios.",
};

export const dynamic = "force-dynamic";

export default async function ArchivoPage() {
  const dates = await getAvailableDates(365);

  // Group by month
  const byMonth: Record<string, typeof dates> = {};
  for (const entry of dates) {
    const monthKey = entry.date.slice(0, 7); // "2026-02"
    if (!byMonth[monthKey]) byMonth[monthKey] = [];
    byMonth[monthKey].push(entry);
  }

  return (
    <div>
      <div className="mb-8">
        <h1
          className="text-2xl md:text-3xl font-bold mb-2"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          Archivo
        </h1>
        <p className="text-muted-foreground">
          Todas las ediciones disponibles del Periódico Financiero.
        </p>
        <div className="rule-bottom mt-4" />
      </div>

      {dates.length === 0 ? (
        <p className="text-muted-foreground text-center py-12">
          No hay ediciones archivadas aún.
        </p>
      ) : (
        <div className="space-y-8">
          {Object.entries(byMonth).map(([monthKey, entries]) => {
            const [year, month] = monthKey.split("-");
            const monthName = new Date(
              parseInt(year),
              parseInt(month) - 1,
              1
            ).toLocaleDateString("es-AR", { month: "long", year: "numeric" });

            return (
              <div key={monthKey}>
                <h2
                  className="text-lg font-semibold mb-3 capitalize"
                  style={{ fontFamily: "var(--font-serif)" }}
                >
                  {monthName}
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                  {entries.map((entry) => (
                    <Link
                      key={entry.date}
                      href={`/archivo/${entry.date}`}
                      className="flex items-center justify-between p-3 bg-card border border-border rounded-sm hover:border-accent hover:shadow-sm transition-all"
                    >
                      <span className="text-sm font-medium">
                        {formatDateFull(entry.date)}
                      </span>
                      <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
                        {entry.reportCount} reportes
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
