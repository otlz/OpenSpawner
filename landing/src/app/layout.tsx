import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";
import { LocaleProvider } from "@/components/i18n/locale-provider";
import { LandingNavbar } from "@/components/landing/landing-navbar";
import { LandingFooter } from "@/components/landing/landing-footer";
import { cn } from "@/lib/utils";
import { SITE_NAME, SITE_URL } from "@/lib/site";
import { resolveLocale } from "@/lib/i18n/detect";
import { getDictionary } from "@/lib/i18n/dictionaries";

const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });

const OG_LOCALES = { de: "de_DE", en: "en_US" } as const;

export async function generateMetadata(): Promise<Metadata> {
  const locale = await resolveLocale();
  const description = getDictionary(locale).metaDescription;

  return {
    metadataBase: new URL(SITE_URL),
    title: {
      default: SITE_NAME,
      template: `%s · ${SITE_NAME}`,
    },
    description,
    openGraph: {
      type: "website",
      locale: OG_LOCALES[locale],
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
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const locale = await resolveLocale();

  return (
    <html
      lang={locale}
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
          <LocaleProvider initialLocale={locale}>
            <div className="flex min-h-dvh flex-col overflow-x-hidden">
              <LandingNavbar />
              <main className="flex-1">{children}</main>
              <LandingFooter />
            </div>
          </LocaleProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
