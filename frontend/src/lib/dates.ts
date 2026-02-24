import { format, parseISO } from "date-fns";
import { es } from "date-fns/locale";

/** "24 de febrero de 2026" */
export function formatDateLong(date: string | Date): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, "d 'de' MMMM 'de' yyyy", { locale: es });
}

/** "24 feb 2026" */
export function formatDateShort(date: string | Date): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  return format(d, "d MMM yyyy", { locale: es });
}

/** "Lunes 24 de febrero de 2026" */
export function formatDateFull(date: string | Date): string {
  const d = typeof date === "string" ? parseISO(date) : date;
  const formatted = format(d, "EEEE d 'de' MMMM 'de' yyyy", { locale: es });
  return formatted.charAt(0).toUpperCase() + formatted.slice(1);
}

/** "2026-02-24" */
export function toISODate(date: Date): string {
  return date.toISOString().split("T")[0];
}

/** Parse "2026-02-24" to Date (UTC noon to avoid timezone issues) */
export function parseDate(dateStr: string): Date {
  return new Date(dateStr + "T00:00:00.000Z");
}
