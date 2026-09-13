import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { Providers } from "@/components/providers";
import { TooltipProvider } from "@/components/ui/tooltip";

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
});

export const metadata: Metadata = {
  title: {
    default: "RAGLens",
    template: "%s — RAGLens",
  },
  description: "Observability and debugging platform for RAG pipelines.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html
      lang="en"
      className={cn("dark", geistSans.variable, geistMono.variable)}
      suppressHydrationWarning
    >
      <body
        className={cn(
          "min-h-screen bg-background font-sans antialiased"
        )}
      >
        <Providers>
          <TooltipProvider>{children}</TooltipProvider>
        </Providers>
      </body>
    </html>
  );
}
