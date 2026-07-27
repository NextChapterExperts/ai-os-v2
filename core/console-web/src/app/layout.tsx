import type { Metadata } from "next";
import { Bricolage_Grotesque, Source_Sans_3, IBM_Plex_Mono, Cinzel } from "next/font/google";
import { AppShell } from "@/components/AppShell";
import "./globals.css";

const display = Bricolage_Grotesque({
  variable: "--font-display",
  subsets: ["latin"],
  weight: ["500", "600", "700"],
});

const body = Source_Sans_3({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600"],
});

const mono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

const cinzel = Cinzel({
  variable: "--font-mystic",
  subsets: ["latin"],
  weight: ["700", "800", "900"],
});

export const metadata: Metadata = {
  title: "VIRKI · Sovereign Enterprise AI OS",
  description: "Souveränes KI-Betriebssystem — Lagebild, Workflows, Plattform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="de">
      <body className={`${display.variable} ${body.variable} ${mono.variable} ${cinzel.variable} antialiased`}>
        <AppShell>{children}</AppShell>
      </body>
    </html>
  );
}
