"use client";

import { Button } from "@/components/ui/button";
import { FadeInView } from "@/components/animation/fade-in-view";
import { GithubIcon } from "@/components/landing/github-icon";
import { useLocale } from "@/components/i18n/locale-provider";
import { GITHUB_URL, SITE_NAME } from "@/lib/site";

export function HeroSection() {
  const { dict } = useLocale();

  return (
    <section className="relative pt-28 pb-12 md:pt-40 md:pb-16">
      <div className="mx-auto w-full max-w-7xl px-4 lg:px-8">
        <FadeInView className="max-w-4xl">
          <h1 className="text-5xl font-semibold tracking-tight sm:text-6xl lg:text-7xl">
            {SITE_NAME}
          </h1>

          <p className="mt-6 max-w-2xl text-xl font-medium tracking-tight text-balance md:text-2xl">
            {dict.hero.lead}
          </p>

          <p className="mt-4 max-w-xl text-base text-muted-foreground md:text-lg">
            {dict.hero.body}
          </p>

          <div className="mt-8">
            <Button size="lg" asChild>
              <a href={GITHUB_URL} target="_blank" rel="noopener noreferrer">
                <GithubIcon />
                {dict.hero.cta}
              </a>
            </Button>
          </div>
        </FadeInView>
      </div>
    </section>
  );
}
