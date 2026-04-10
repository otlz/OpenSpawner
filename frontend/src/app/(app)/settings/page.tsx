'use client'

import { useAuth } from '@/hooks/use-auth'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'

export default function SettingsPage() {
  const { user, isLoading } = useAuth()

  if (isLoading || !user) {
    return (
      <>
        <div className="mb-6">
          <Skeleton className="h-8 w-48 mb-2" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid gap-6">
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

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Einstellungen</h2>
        <p className="text-muted-foreground">
          Verwalte deine Account-Einstellungen
        </p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Profil</CardTitle>
            <CardDescription>Deine Account-Informationen</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <span className="text-sm font-medium text-muted-foreground">E-Mail</span>
              <p className="text-base font-semibold">{user?.email}</p>
            </div>
            <div>
              <span className="text-sm font-medium text-muted-foreground">Benutzername</span>
              <p className="text-base font-semibold">{user?.slug}</p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-muted-foreground">Status</span>
              <Badge variant={user?.state === 'verified' ? 'default' : 'secondary'}>
                {user?.state === 'verified' ? 'Verifiziert' : user?.state === 'active' ? 'Aktiv' : 'Registriert'}
              </Badge>
            </div>
            {user?.is_admin && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-muted-foreground">Rolle</span>
                <Badge variant="default">Administrator</Badge>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Account-Info</CardTitle>
            <CardDescription>Zusätzliche Informationen</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {user?.created_at && (
              <div>
                <span className="text-sm font-medium text-muted-foreground">Erstellt am</span>
                <p className="text-base font-semibold">
                  {new Date(user.created_at).toLocaleString('de-DE')}
                </p>
              </div>
            )}
            {user?.last_used && (
              <div>
                <span className="text-sm font-medium text-muted-foreground">Zuletzt verwendet</span>
                <p className="text-base font-semibold">
                  {new Date(user.last_used).toLocaleString('de-DE')}
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  )
}
