import type { Metadata } from "next";

import { ObfuscatedEmail } from "@/components/landing/obfuscated-email";

export const metadata: Metadata = {
  title: "Impressum",
  description: "Impressum und Anbieterkennzeichnung von OpenSpawner.",
  robots: { index: false, follow: true },
};

const PROVIDER_ADDRESS = [
  "Karl Kübel Schule Bensheim",
  "Berliner Ring 34-38",
  "64625 Bensheim",
];

export default function ImpressumPage() {
  return (
    <section className="pt-28 pb-20 md:pt-32 md:pb-28">
      <div className="mx-auto w-full max-w-3xl px-4 lg:px-8">
        <h1 className="text-3xl font-semibold tracking-tight md:text-4xl">
          Impressum
        </h1>

        <div className="mt-10 space-y-10 hyphens-auto text-justify text-sm leading-relaxed text-muted-foreground">
          {/* Anbieter */}
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Angaben gemäß § 5 DDG
            </h2>
            <p className="whitespace-pre-line">
              {["OpenSpawner", "Rainer Wieland und Navin Dass", ...PROVIDER_ADDRESS].join(
                "\n",
              )}
            </p>
          </div>

          {/* Kontakt */}
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Kontakt
            </h2>
            <p>
              E-Mail: <ObfuscatedEmail user="info" domain="karlkuebelschule.de" />
            </p>
          </div>

          {/* Verantwortlich für den Inhalt */}
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Verantwortlich für den Inhalt nach § 18 Abs. 2 MStV
            </h2>
            <p className="whitespace-pre-line">
              {["Rainer Wieland und Navin Dass", ...PROVIDER_ADDRESS].join("\n")}
            </p>
          </div>

          {/* Haftung für Inhalte */}
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Haftung für Inhalte
            </h2>
            <p>
              Als Diensteanbieter sind wir gemäß § 7 Abs. 1 DDG für eigene
              Inhalte auf diesen Seiten nach den allgemeinen Gesetzen
              verantwortlich. Nach §§ 8 bis 10 DDG sind wir als Diensteanbieter
              jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde
              Informationen zu überwachen oder nach Umständen zu forschen, die
              auf eine rechtswidrige Tätigkeit hinweisen. Verpflichtungen zur
              Entfernung oder Sperrung der Nutzung von Informationen nach den
              allgemeinen Gesetzen bleiben hiervon unberührt. Eine
              diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der
              Kenntnis einer konkreten Rechtsverletzung möglich. Bei
              Bekanntwerden von entsprechenden Rechtsverletzungen werden wir
              diese Inhalte umgehend entfernen.
            </p>
          </div>

          {/* Haftung für Links */}
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Haftung für Links
            </h2>
            <p>
              Unser Angebot enthält Links zu externen Websites Dritter, auf
              deren Inhalte wir keinen Einfluss haben. Deshalb können wir für
              diese fremden Inhalte auch keine Gewähr übernehmen. Für die
              Inhalte der verlinkten Seiten ist stets der jeweilige Anbieter
              oder Betreiber der Seiten verantwortlich. Die verlinkten Seiten
              wurden zum Zeitpunkt der Verlinkung auf mögliche Rechtsverstöße
              überprüft. Rechtswidrige Inhalte waren zum Zeitpunkt der
              Verlinkung nicht erkennbar. Eine permanente inhaltliche Kontrolle
              der verlinkten Seiten ist jedoch ohne konkrete Anhaltspunkte einer
              Rechtsverletzung nicht zumutbar. Bei Bekanntwerden von
              Rechtsverletzungen werden wir derartige Links umgehend entfernen.
            </p>
          </div>

          {/* Urheberrecht */}
          <div>
            <h2 className="mb-3 text-lg font-semibold text-foreground">
              Urheberrecht
            </h2>
            <p>
              Die durch die Seitenbetreiber erstellten Inhalte und Werke auf
              diesen Seiten unterliegen dem deutschen Urheberrecht. Die
              Vervielfältigung, Bearbeitung, Verbreitung und jede Art der
              Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der
              schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers.
              Downloads und Kopien dieser Seite sind nur für den privaten,
              nicht kommerziellen Gebrauch gestattet. Soweit die Inhalte auf
              dieser Seite nicht vom Betreiber erstellt wurden, werden die
              Urheberrechte Dritter beachtet. Insbesondere werden Inhalte
              Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine
              Urheberrechtsverletzung aufmerksam werden, bitten wir um einen
              entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen
              werden wir derartige Inhalte umgehend entfernen.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
