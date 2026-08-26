import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "TokoMate AI",
  description: "Bilingual AI customer support for Indonesian SMEs",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="id">
      <body>{children}</body>
    </html>
  );
}

