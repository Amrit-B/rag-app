import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  metadataBase: new URL("https://amritb.me"),
  title: {
    default: "Agentic RAG Platform | Amrit Bhaganagare",
    template: "%s | Amrit Bhaganagare",
  },
  description:
    "Enterprise-grade Self-Reflective RAG platform built with LangGraph, LanceDB, Gemini 2.5 Flash, Tavily live web fallback, and Prometheus observability.",
  keywords: [
    "Amrit Bhaganagare",
    "amritb.me",
    "Agentic RAG",
    "Self-Reflective RAG",
    "LangGraph",
    "LanceDB",
    "Gemini Embeddings",
    "Tavily Search",
    "Model Context Protocol",
    "MCP",
    "RAG Observability",
    "FastAPI",
    "Next.js 15",
  ],
  authors: [{ name: "Amrit Bhaganagare", url: "https://amritb.me" }],
  creator: "Amrit Bhaganagare",
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://amritb.me",
    title: "Agentic RAG Platform | Amrit Bhaganagare",
    description:
      "Enterprise Self-Reflective RAG platform powered by LangGraph, LanceDB, and Gemini.",
    siteName: "Amrit Bhaganagare - AI Engineering",
  },
  twitter: {
    card: "summary_large_image",
    title: "Agentic RAG Platform | Amrit Bhaganagare",
    description:
      "Enterprise Self-Reflective RAG platform powered by LangGraph, LanceDB, and Gemini.",
  },
  robots: {
    index: true,
    follow: true,
  },
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
