import Link from "next/link";
import { PackageOpen } from "lucide-react";

import { Button } from "@/components/ui/button";
import { GithubIcon } from "@/components/landing/github-icon";
import { LanguageToggle } from "@/components/landing/language-toggle";
import { GITHUB_URL, SITE_NAME } from "@/lib/site";

export function LandingNavbar() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 h-14 bg-background/50 backdrop-blur-xl backdrop-saturate-150">
      <nav className="mx-auto flex h-full w-full max-w-7xl items-center justify-between px-4 lg:px-8">
        <Link href="/" className="flex items-center gap-2">
          <PackageOpen className="size-6" />
          <span className="whitespace-nowrap text-[20px] font-semibold tracking-tight">
            {SITE_NAME}
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <LanguageToggle />
          <Button variant="outline" asChild>
            <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
              <GithubIcon />
              GitHub
            </a>
          </Button>
        </div>
      </nav>
    </header>
  );
}
