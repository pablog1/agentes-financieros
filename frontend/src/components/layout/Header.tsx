"use client";

import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";
import { useState } from "react";

export function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="border-b border-border">
      {/* Top rule */}
      <div className="rule-double" />

      {/* Masthead */}
      <div className="max-w-6xl mx-auto px-4 py-4 text-center">
        <Link href="/" className="inline-block">
          <h1
            className="text-3xl md:text-4xl font-bold tracking-tight"
            style={{ fontFamily: "var(--font-serif)" }}
          >
            El Periódico Financiero
          </h1>
        </Link>
        <p className="text-muted-foreground text-sm mt-1 tracking-widest uppercase">
          7 analistas IA &middot; Un mercado
        </p>
      </div>

      {/* Navigation */}
      <nav className="border-t border-border">
        <div className="max-w-6xl mx-auto px-4 flex items-center justify-between h-10">
          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-6 text-sm">
            <Link href="/" className="hover:text-accent transition-colors font-medium">
              Edición del día
            </Link>
            <Link href="/archivo" className="hover:text-accent transition-colors">
              Archivo
            </Link>
            <span className="text-border">|</span>
            <Link href="/analista/manu" className="hover:text-accent transition-colors">Manu</Link>
            <Link href="/analista/tomi" className="hover:text-accent transition-colors">Tomi</Link>
            <Link href="/analista/vale" className="hover:text-accent transition-colors">Vale</Link>
            <Link href="/analista/santi" className="hover:text-accent transition-colors">Santi</Link>
            <Link href="/analista/sol" className="hover:text-accent transition-colors">Sol</Link>
            <Link href="/analista/diego" className="hover:text-accent transition-colors">Diego</Link>
            <Link href="/analista/roberto" className="hover:text-accent transition-colors">Roberto</Link>
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-1"
            onClick={() => setMenuOpen(!menuOpen)}
            aria-label="Menu"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {menuOpen ? (
                <path d="M18 6L6 18M6 6l12 12" />
              ) : (
                <>
                  <line x1="3" y1="6" x2="21" y2="6" />
                  <line x1="3" y1="12" x2="21" y2="12" />
                  <line x1="3" y1="18" x2="21" y2="18" />
                </>
              )}
            </svg>
          </button>

          <ThemeToggle />
        </div>

        {/* Mobile menu */}
        {menuOpen && (
          <div className="md:hidden border-t border-border px-4 py-3 flex flex-col gap-2 text-sm">
            <Link href="/" onClick={() => setMenuOpen(false)} className="py-1 font-medium">
              Edición del día
            </Link>
            <Link href="/archivo" onClick={() => setMenuOpen(false)} className="py-1">
              Archivo
            </Link>
            <hr className="border-border" />
            {["manu", "tomi", "vale", "santi", "sol", "diego", "roberto"].map((a) => (
              <Link key={a} href={`/analista/${a}`} onClick={() => setMenuOpen(false)} className="py-1 capitalize">
                {a.charAt(0).toUpperCase() + a.slice(1)}
              </Link>
            ))}
          </div>
        )}
      </nav>
    </header>
  );
}
