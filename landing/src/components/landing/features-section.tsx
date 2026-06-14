"use client";

import {
  Container,
  LayoutGrid,
  MailCheck,
  Server,
  ShieldCheck,
  TimerOff,
  type LucideIcon,
} from "lucide-react";

import {
  FadeInView,
  StaggerContainer,
  StaggerItem,
} from "@/components/animation/fade-in-view";
import { useLocale } from "@/components/i18n/locale-provider";
import type { Dictionary } from "@/lib/i18n/dictionaries";

// Pairs each feature's icon with its dictionary key. The order here is the
// order shown; the title and description come from the active language.
const FEATURES: { key: keyof Dictionary["features"]["items"]; Icon: LucideIcon }[] =
  [
    { key: "passwordless", Icon: MailCheck },
    { key: "isolated", Icon: Container },
    { key: "catalog", Icon: LayoutGrid },
    { key: "cleanup", Icon: TimerOff },
    { key: "production", Icon: ShieldCheck },
    { key: "openSource", Icon: Server },
  ];

function FeatureCard({
  Icon,
  title,
  description,
}: {
  Icon: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="flex h-full flex-col rounded-xl border border-border/50 bg-card p-6 shadow-sm transition-colors hover:border-border">
      <span className="mb-4 inline-flex size-11 items-center justify-center rounded-lg bg-muted text-foreground">
        <Icon className="size-5" />
      </span>
      <h3 className="text-base font-medium">{title}</h3>
      <p className="mt-2 flex-1 text-sm text-muted-foreground">{description}</p>
    </div>
  );
}

export function FeaturesSection() {
  const { dict } = useLocale();

  return (
    <section id="features" className="scroll-mt-20 py-16 md:py-24">
      <div className="mx-auto w-full max-w-7xl px-4 lg:px-8">
        <FadeInView className="mb-12 max-w-2xl">
          <h2 className="mb-4 text-2xl font-semibold tracking-tight md:text-3xl">
            {dict.features.heading}
          </h2>
          <p className="text-muted-foreground">{dict.features.intro}</p>
        </FadeInView>

        <StaggerContainer
          className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3"
          staggerDelay={0.1}
        >
          {FEATURES.map(({ key, Icon }) => {
            const item = dict.features.items[key];
            return (
              <StaggerItem key={key}>
                <FeatureCard
                  Icon={Icon}
                  title={item.title}
                  description={item.description}
                />
              </StaggerItem>
            );
          })}
        </StaggerContainer>
      </div>
    </section>
  );
}
