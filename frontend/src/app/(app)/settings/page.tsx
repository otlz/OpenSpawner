'use client'

import { useCallback, useRef, useState } from 'react'
import { useAuth } from '@/hooks/use-auth'
import { api } from '@/lib/api'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Avatar, AvatarImage, AvatarFallback } from '@/components/ui/avatar'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { ImageCrop, ImageCropContent, ImageCropApply } from '@/components/ui/image-crop'
import { toast } from 'sonner'
import { Camera, Trash2, Loader2, CropIcon } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

/** Convert a data URL to a File object */
function dataUrlToFile(dataUrl: string, filename: string): File {
  const [header, base64] = dataUrl.split(',')
  const mime = header.match(/:(.*?);/)?.[1] || 'image/png'
  const binary = atob(base64)
  const array = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i++) {
    array[i] = binary.charCodeAt(i)
  }
  return new File([array], filename, { type: mime })
}

export default function SettingsPage() {
  const { user, isLoading, refreshUser } = useAuth()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  // Crop dialog state
  const [cropDialogOpen, setCropDialogOpen] = useState(false)
  const [cropFile, setCropFile] = useState<File | null>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Client-side validation
    const allowedTypes = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
    if (!allowedTypes.includes(file.type)) {
      toast.error('Ungültiges Dateiformat. Erlaubt: PNG, JPG, GIF, WebP')
      return
    }
    if (file.size > 2 * 1024 * 1024) {
      toast.error('Datei zu groß. Maximal 2 MB erlaubt')
      return
    }

    // Open crop dialog
    setCropFile(file)
    setCropDialogOpen(true)

    // Reset file input so re-selecting same file works
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleCropComplete = useCallback(async (croppedDataUrl: string) => {
    // Close dialog immediately
    setCropDialogOpen(false)

    const file = dataUrlToFile(croppedDataUrl, 'avatar.png')

    setIsUploading(true)
    const { data, error } = await api.uploadAvatar(file)
    setIsUploading(false)

    if (error) {
      toast.error(error)
      return
    }

    toast.success(data?.message || 'Avatar hochgeladen')
    await refreshUser()

    // Clean up
    setCropFile(null)
  }, [refreshUser])

  const handleCropCancel = () => {
    setCropDialogOpen(false)
    setCropFile(null)
  }

  const handleAvatarDelete = async () => {
    setIsDeleting(true)
    const { data, error } = await api.deleteAvatar()
    setIsDeleting(false)

    if (error) {
      toast.error(error)
      return
    }

    toast.success(data?.message || 'Avatar gelöscht')
    await refreshUser()
  }

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
              <div className="flex items-center gap-4">
                <Skeleton className="h-20 w-20 rounded-full" />
                <div className="space-y-2">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-8 w-24" />
                </div>
              </div>
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

  const avatarSrc = user.avatar_url ? `${API_BASE}${user.avatar_url}` : undefined

  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-bold">Einstellungen</h2>
        <p className="text-muted-foreground">
          Profil und Kontoinformationen
        </p>
      </div>

      <div className="grid gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Profil</CardTitle>
            <CardDescription>Profilbild, E-Mail, Benutzername und Status</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="relative group">
                <Avatar className="h-20 w-20">
                  {avatarSrc && (
                    <AvatarImage src={avatarSrc} alt="Profilbild" />
                  )}
                  <AvatarFallback className="text-2xl">
                    {user.email?.charAt(0).toUpperCase() || 'U'}
                  </AvatarFallback>
                </Avatar>
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  disabled={isUploading}
                  className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
                >
                  {isUploading ? (
                    <Loader2 className="h-6 w-6 text-white animate-spin" />
                  ) : (
                    <Camera className="h-6 w-6 text-white" />
                  )}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/png,image/jpeg,image/gif,image/webp"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
              <div className="space-y-1">
                <p className="text-sm text-muted-foreground">
                  Profilbild (max. 2 MB)
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isUploading}
                  >
                    {isUploading ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Hochladen...
                      </>
                    ) : (
                      <>
                        <Camera className="h-4 w-4" />
                        {user.avatar_url ? 'Ändern' : 'Hochladen'}
                      </>
                    )}
                  </Button>
                  {user.avatar_url && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleAvatarDelete}
                      disabled={isDeleting}
                      className="text-destructive hover:text-destructive"
                    >
                      {isDeleting ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <>
                          <Trash2 className="h-4 w-4" />
                          Entfernen
                        </>
                      )}
                    </Button>
                  )}
                </div>
              </div>
            </div>
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
            <CardDescription>Erstellungsdatum und Aktivität</CardDescription>
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

      {/* Avatar Crop Dialog */}
      <Dialog open={cropDialogOpen} onOpenChange={(open) => { if (!open) handleCropCancel() }}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Bild zuschneiden</DialogTitle>
            <DialogDescription>
              Wähle den Ausschnitt für dein Profilbild.
            </DialogDescription>
          </DialogHeader>
          {cropFile && (
            <ImageCrop
              file={cropFile}
              aspect={1}
              circularCrop
              maxImageSize={2 * 1024 * 1024}
              onCrop={handleCropComplete}
            >
              <div className="flex flex-col items-center gap-4">
                <ImageCropContent className="max-h-[350px] rounded-md" />
              </div>
              <DialogFooter className="gap-2 sm:gap-0 mt-4">
                <Button variant="outline" onClick={handleCropCancel}>
                  Abbrechen
                </Button>
                <ImageCropApply variant="default" size="default">
                  <CropIcon className="h-4 w-4 mr-2" />
                  Übernehmen
                </ImageCropApply>
              </DialogFooter>
            </ImageCrop>
          )}
        </DialogContent>
      </Dialog>
    </>
  )
}
