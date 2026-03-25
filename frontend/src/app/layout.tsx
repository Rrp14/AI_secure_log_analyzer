import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "AI Secure Log Analyzer",
  description: "AI-powered security log analysis, anomaly detection, and real-time threat monitoring",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <div className="app-shell">
          <Sidebar />
          <div className="main-area">
            <header className="topbar">
              <span className="topbar-title">Security Operations Center</span>
              <div className="topbar-right">
                <span style={{ fontSize: '0.8rem', color: 'var(--on-surface-variant)' }}>
                  System Active
                </span>
                <span className="status-dot online" />
              </div>
            </header>
            <main className="page-content">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  );
}
