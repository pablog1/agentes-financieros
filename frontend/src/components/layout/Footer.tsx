export function Footer() {
  return (
    <footer className="border-t border-border mt-16">
      <div className="max-w-6xl mx-auto px-4 py-8 text-center text-sm text-muted-foreground">
        <p style={{ fontFamily: "var(--font-serif)" }} className="text-lg font-semibold text-foreground mb-2">
          El Periódico Financiero
        </p>
        <p>
          7 analistas IA generan reportes diarios sobre el mercado argentino y global.
        </p>
        <p className="mt-2">
          Los reportes son generados por inteligencia artificial y no constituyen asesoramiento financiero.
        </p>
        <div className="mt-4 pt-4 border-t border-border text-xs">
          <p>Hecho con Next.js, Prisma y Claude &middot; {new Date().getFullYear()}</p>
        </div>
      </div>
    </footer>
  );
}
