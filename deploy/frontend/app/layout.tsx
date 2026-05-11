import type { Metadata } from "next";
import { Geist_Mono, Oswald } from "next/font/google";
import "./globals.css";

const oswald = Oswald({
  variable: "--font-oswald",
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Uninorma",
  description: "Consulta la normatividad institucional de la Universidad del Norte en lenguaje natural.",
  icons: {
    icon: "/uninorte_tree.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es">
      <body
        className={`${oswald.variable} ${oswald.className} ${geistMono.variable} antialiased`}
      >
        {children}
      </body>
    </html>
  );
}
