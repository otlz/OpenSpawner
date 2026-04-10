import { Skeleton } from "@/components/ui/skeleton"
import { Card, CardContent } from "@/components/ui/card"

export default function LoginLoading() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center bg-muted p-6 md:p-10">
      <div className="w-full max-w-sm md:max-w-4xl">
        <div className="flex flex-col gap-6">
          <Card className="overflow-hidden p-0">
            <CardContent className="grid p-0 md:grid-cols-2">
              {/* Form side */}
              <div className="p-6 md:p-8">
                <div className="flex flex-col gap-6">
                  <div className="flex flex-col items-center gap-2">
                    <Skeleton className="h-8 w-32" />
                    <Skeleton className="h-4 w-64" />
                  </div>
                  <div className="grid gap-2">
                    <Skeleton className="h-4 w-12" />
                    <Skeleton className="h-10 w-full rounded-md" />
                  </div>
                  <Skeleton className="h-10 w-full rounded-md" />
                  <Skeleton className="h-4 w-72 mx-auto" />
                </div>
              </div>
              {/* Branding side */}
              <div className="relative hidden bg-primary md:flex md:flex-col md:items-center md:justify-center">
                <div className="flex flex-col items-center gap-4 p-8">
                  <Skeleton className="h-16 w-16 rounded bg-primary-foreground/20" />
                  <div className="flex flex-col items-center gap-2">
                    <Skeleton className="h-8 w-40 bg-primary-foreground/20" />
                    <Skeleton className="h-4 w-56 bg-primary-foreground/20" />
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}
