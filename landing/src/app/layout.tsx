import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { LandingNavbar } from "@/components/landing/landing-navbar";
import { LandingFooter } from "@/components/landing/landing-footer";
import { cn } from "@/lib/utils";
import { SITE_NAME, SITE_URL } from "@/lib/site";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

const description =
  "OpenSpawner ist eine selbst gehostete Open-Source-Plattform, die isolierte Docker-Container pro Nutzer bereitstellt: passwortloser Login, Vorlagen-Katalog und automatisches Aufräumen.";

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: SITE_NAME,
    template: `%s · ${SITE_NAME}`,
  },
  description,
  openGraph: {
    type: "website",
    locale: "de_DE",
    siteName: SITE_NAME,
    url: SITE_URL,
    title: SITE_NAME,
    description,
  },
  twitter: {
    card: "summary",
    title: SITE_NAME,
    description,
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="de"
      className={cn("font-sans antialiased", geist.variable)}
      suppressHydrationWarning
    >
      <body suppressHydrationWarning>
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex min-h-dvh flex-col overflow-x-hidden">
            <LandingNavbar />
            <main className="flex-1">{children}</main>
            <LandingFooter />
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
