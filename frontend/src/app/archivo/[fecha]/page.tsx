import { notFound } from "next/navigation";
import { getReportsByDate, getDailyData } from "@/lib/queries";
import { EditionHeader } from "@/components/home/EditionHeader";
import { MarketTicker } from "@/components/home/MarketTicker";
import { ReportGrid } from "@/components/home/ReportGrid";
import { formatDateLong } from "@/lib/dates";
import Link from "next/link";
import type { Metadata } from "next";
import type { ReportWithAgent } from "@/types";

interface PageProps {
  params: Promise<{ fecha: string }>;
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { fecha } = await params;
  return {
    title: `${formatDateLong(fecha)} — Archivo — El Periódico Financiero`,
  };
}

export default async function ArchivoFechaPage({ params }: PageProps) {
  const { fecha } = await params;
  const reports = (await getReportsByDate(new Date(fecha + "T00:00:00.000Z"))) as ReportWithAgent[];
  const dailyData = await getDailyData(fecha);

  if (reports.length === 0) notFound();

  return (
    <div>
      <nav className="text-sm text-muted-foreground mb-6 flex items-center gap-1.5">
        <Link href="/" className="hover:text-accent transition-colors">Inicio</Link>
        <span>/</span>
        <Link href="/archivo" className="hover:text-accent transition-colors">Archivo</Link>
        <span>/</span>
        <span>{formatDateLong(fecha)}</span>
      </nav>

      <EditionHeader date={fecha} reportCount={reports.length} />
      <MarketTicker data={dailyData} />
      <ReportGrid reports={reports} />
    </div>
  );
}
