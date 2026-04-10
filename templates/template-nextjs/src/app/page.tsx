import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Container, Rocket, Code, Terminal } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/50">
      {/* Header */}
      <header className="border-b bg-background/80 backdrop-blur-sm">
        <div className="container mx-auto flex h-16 items-center px-4">
          <div className="flex items-center gap-2">
            <Container className="h-6 w-6 text-primary" />
            <span className="text-lg font-semibold">Mein Container</span>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16">
        <div className="mx-auto max-w-3xl text-center">
          <div className="mb-6 inline-flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
            <Rocket className="h-8 w-8 text-primary" />
          </div>
          <h1 className="mb-4 text-4xl font-bold tracking-tight sm:text-5xl">
            Willkommen in deinem Container!
          </h1>
          <p className="mb-8 text-lg text-muted-foreground">
            Dies ist dein persoenlicher Bereich. Du kannst diese Seite anpassen
            und eigene Anwendungen deployen.
          </p>
        </div>

        {/* Feature Cards */}
        <div className="mx-auto mt-16 grid max-w-4xl gap-6 md:grid-cols-2">
          <Card>
            <CardHeader>
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Code className="h-5 w-5 text-primary" />
              </div>
              <CardTitle>Entwicklung</CardTitle>
              <CardDescription>
                Starte hier mit deiner eigenen Anwendung
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Dieses Template basiert auf Next.js und React. Du kannst es
                anpassen oder komplett ersetzen.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="mb-2 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                <Terminal className="h-5 w-5 text-primary" />
              </div>
              <CardTitle>Technologie</CardTitle>
              <CardDescription>Moderne Tools für moderne Apps</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2 text-sm text-muted-foreground">
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  Next.js 14 mit App Router
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  TypeScript für Typsicherheit
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  Tailwind CSS für Styling
                </li>
                <li className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  shadcn/ui Komponenten
                </li>
              </ul>
            </CardContent>
          </Card>
        </div>

        {/* CTA Section */}
        <div className="mx-auto mt-16 max-w-xl text-center">
          <Card className="bg-primary/5 border-primary/20">
            <CardContent className="pt-6">
              <h2 className="mb-2 text-xl font-semibold">Bereit loszulegen?</h2>
              <p className="mb-4 text-sm text-muted-foreground">
                Bearbeite die Dateien im Container, um diese Seite anzupassen.
              </p>
              <div className="flex justify-center gap-2">
                <Button variant="outline" asChild>
                  <a
                    href="https://nextjs.org/docs"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Next.js Docs
                  </a>
                </Button>
                <Button variant="outline" asChild>
                  <a
                    href="https://ui.shadcn.com"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    shadcn/ui
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-16">
        <div className="container mx-auto flex h-16 items-center justify-center px-4">
          <p className="text-sm text-muted-foreground">
            OpenSpawner - Your personal development environment
          </p>
        </div>
      </footer>
    </div>
  );
}
