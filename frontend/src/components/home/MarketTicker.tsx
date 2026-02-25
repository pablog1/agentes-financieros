interface MarketTickerProps {
  data: Record<string, unknown> | null;
}

interface TickerItem {
  label: string;
  value: string;
  change?: string;
  positive?: boolean;
}

function fmt(val: number, decimals = 0): string {
  const parts = val.toFixed(decimals).split(".");
  parts[0] = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  return parts.join(",");
}

function extractTickers(data: Record<string, unknown>): TickerItem[] {
  const items: TickerItem[] = [];
  const macro = data.macro as Record<string, unknown> | undefined;
  const indices = data.indices as Record<string, Record<string, number>> | undefined;
  const crypto = data.crypto as Record<string, Record<string, number>> | undefined;

  // Dólar oficial
  const dolar = macro?.dolar as Record<string, Record<string, number>> | undefined;
  if (dolar?.oficial?.venta) {
    items.push({ label: "Dólar Oficial", value: `$${fmt(dolar.oficial.venta)}` });
  }
  if (dolar?.blue?.venta) {
    items.push({ label: "Dólar Blue", value: `$${fmt(dolar.blue.venta)}` });
  }
  if (dolar?.ccl?.venta) {
    items.push({ label: "CCL", value: `$${fmt(dolar.ccl.venta, 1)}` });
  }

  // Riesgo país
  const rp = macro?.riesgo_pais as Record<string, number> | undefined;
  if (rp?.valor) {
    items.push({ label: "Riesgo País", value: `${fmt(rp.valor)} pts` });
  }

  // MERVAL
  if (indices?.MERVAL?.ultimo) {
    const merval = indices.MERVAL;
    const change = merval.variacion_pct;
    items.push({
      label: "MERVAL",
      value: fmt(merval.ultimo),
      change: change != null ? `${change >= 0 ? "+" : ""}${fmt(change, 1)}%` : undefined,
      positive: change >= 0,
    });
  }

  // S&P 500
  if (indices?.SP500?.ultimo) {
    const sp = indices.SP500;
    const change = sp.variacion_pct;
    items.push({
      label: "S&P 500",
      value: fmt(sp.ultimo),
      change: change != null ? `${change >= 0 ? "+" : ""}${fmt(change, 1)}%` : undefined,
      positive: change >= 0,
    });
  }

  // BTC
  if (crypto?.BTC?.ultimo) {
    const btc = crypto.BTC;
    const change = btc.variacion_pct;
    items.push({
      label: "BTC",
      value: `USD ${fmt(btc.ultimo)}`,
      change: change != null ? `${change >= 0 ? "+" : ""}${fmt(change, 1)}%` : undefined,
      positive: change >= 0,
    });
  }

  // Inflación
  const inflacion = macro?.inflacion as Record<string, number> | undefined;
  if (inflacion?.mensual) {
    items.push({ label: "Inflación", value: `${fmt(inflacion.mensual, 1)}% mensual` });
  }

  return items;
}

export function MarketTicker({ data }: MarketTickerProps) {
  if (!data) return null;

  const items = extractTickers(data);
  if (items.length === 0) return null;

  return (
    <div className="mb-6">
      <div className="flex flex-wrap gap-x-1.5 gap-y-1.5 justify-center">
        {items.map((item) => (
          <div
            key={item.label}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm text-xs font-medium border border-border bg-muted/50"
            style={{ fontVariantNumeric: "tabular-nums" }}
          >
            <span className="text-muted-foreground uppercase tracking-wide" style={{ fontSize: "0.65rem" }}>
              {item.label}
            </span>
            <span className="font-semibold">{item.value}</span>
            {item.change && (
              <span
                className="font-semibold"
                style={{ color: item.positive ? "#16a34a" : "#dc2626" }}
              >
                {item.change}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
