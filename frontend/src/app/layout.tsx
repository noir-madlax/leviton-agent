import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/contexts/auth-context";
import { Toaster } from "@/components/ui/toaster";
import { PostHogAppProvider } from "./providers";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Xenith - AI Agent for marketing data analysis",
  description: "AI-powered data analysis and chart generation tool for marketing",
  icons: {
    icon: [
      {
        url: "/logo-icon-0617-scarlett.svg",
        type: "image/svg+xml",
      },
      {
        url: "/favicon.ico",
        type: "image/x-icon",
      }
    ],
    shortcut: "/logo-icon-0617-scarlett.svg",
    apple: "/logo-icon-0617-scarlett.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body
        className={`${inter.variable} font-sans antialiased`}
      >
        <PostHogAppProvider>
          <AuthProvider>
            {children}
          </AuthProvider>
          <Toaster />
        </PostHogAppProvider>
      </body>
    </html>
  );
}
