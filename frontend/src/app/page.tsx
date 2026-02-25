import { getLatestReports, getLatestDate, getDailyData } from "@/lib/queries";
import { EditionHeader } from "@/components/home/EditionHeader";
import { MarketTicker } from "@/components/home/MarketTicker";
import { ReportGrid } from "@/components/home/ReportGrid";
import type { ReportWithAgent } from "@/types";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const reports = (await getLatestReports()) as ReportWithAgent[];
  const latestDate = await getLatestDate();
  const dailyData = latestDate ? await getDailyData(latestDate) : null;

  if (!latestDate || reports.length === 0) {
    return (
      <div className="text-center py-20">
        <h2
          className="text-2xl font-bold mb-4"
          style={{ fontFamily: "var(--font-serif)" }}
        >
          El Periódico Financiero
        </h2>
        <p className="text-muted-foreground mb-2">
          Aún no hay reportes cargados.
        </p>
        <p className="text-sm text-muted-foreground">
          Ejecutá <code className="bg-muted px-2 py-0.5 rounded text-xs">python3 scripts/push_to_db.py</code> para cargar los reportes.
        </p>
      </div>
    );
  }

  return (
    <>
      <EditionHeader date={latestDate} reportCount={reports.length} />
      <MarketTicker data={dailyData} />
      <ReportGrid reports={reports} />
    </>
  );
}
