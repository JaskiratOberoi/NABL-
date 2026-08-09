import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NDC Quality Records",
  description:
    "Noble Diagnostic Centre — quality record capture and controlled-copy form generation for NDC-DI",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full flex flex-col bg-slate-50 text-slate-900">
        {children}
      </body>
    </html>
  );
}
