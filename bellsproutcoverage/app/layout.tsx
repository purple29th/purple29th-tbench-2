import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "BellsproutCoverage.ai - Codimango Team Task Coverage & Auto-Factory",
  description: "Map team tasks to domain coverage, visualize gaps in systems_and_infra, auto-generate tasks that pass all validations",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
