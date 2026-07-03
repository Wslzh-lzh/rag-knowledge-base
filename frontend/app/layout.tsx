import "./globals.css";

import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "RAG Knowledge Base",
  description: "Enterprise RAG knowledge base workspace"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}

