import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Watad AridOS RFQ Copilot",
  description: "Operator console for the AridOS RFQ Copilot MVP.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
