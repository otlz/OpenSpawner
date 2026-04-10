import { Skeleton } from "@/components/ui/skeleton"
import {
  Card,
  CardContent,
  CardHeader,
} from "@/components/ui/card"

export default function SettingsLoading() {
  return (
    <>
      <div className="mb-6">
        <Skeleton className="h-8 w-48 mb-2" />
        <Skeleton className="h-4 w-64" />
      </div>

      <div className="grid gap-6">
        {/* Profil card */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-16 mb-1" />
            <Skeleton className="h-4 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Skeleton className="h-3 w-14 mb-1.5" />
              <Skeleton className="h-5 w-52" />
            </div>
            <div>
              <Skeleton className="h-3 w-24 mb-1.5" />
              <Skeleton className="h-5 w-36" />
            </div>
            <div className="flex items-center gap-2">
              <Skeleton className="h-3 w-14" />
              <Skeleton className="h-5 w-20 rounded-full" />
            </div>
          </CardContent>
        </Card>

        {/* Account-Info card */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-28 mb-1" />
            <Skeleton className="h-4 w-48" />
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Skeleton className="h-3 w-20 mb-1.5" />
              <Skeleton className="h-5 w-40" />
            </div>
            <div>
              <Skeleton className="h-3 w-28 mb-1.5" />
              <Skeleton className="h-5 w-40" />
            </div>
          </CardContent>
        </Card>
      </div>
    </>
  )
}
