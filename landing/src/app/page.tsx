import { HeroSection } from "@/components/landing/hero-section";
import { PreviewSection } from "@/components/landing/preview-section";
import { FeaturesSection } from "@/components/landing/features-section";
import { CTASection } from "@/components/landing/cta-section";

export default function LandingPage() {
  return (
    <>
      <HeroSection />
      <PreviewSection />
      <FeaturesSection />
      <CTASection />
    </>
  );
}
