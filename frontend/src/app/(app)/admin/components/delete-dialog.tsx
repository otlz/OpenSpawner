/** Bestätigungsdialog für Bulk-Löschung von Containern. */

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface DeleteDialogData {
  containerIds: number[];
  userSummary: { email: string; count: number }[];
}

interface DeleteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  data: DeleteDialogData | null;
  onConfirm: () => void;
}

export default function DeleteDialog({ open, onOpenChange, data, onConfirm }: DeleteDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Container wirklich löschen?</AlertDialogTitle>
          <AlertDialogDescription>
            {data && (
              <>
                <p className="mb-3">
                  Du bist dabei, <strong>{data.containerIds.length} Container</strong> von{" "}
                  <strong>{data.userSummary.length} Benutzer(n)</strong> zu löschen.
                </p>
                <div className="mt-3 space-y-1 text-sm bg-muted/50 p-3 rounded">
                  <p className="font-semibold text-foreground">Betroffene Benutzer:</p>
                  <ul className="space-y-1 ml-2">
                    {data.userSummary.map((user, idx) => (
                      <li key={idx} className="text-sm">
                        - <span className="font-medium">{user.email}</span> ({user.count} Container)
                      </li>
                    ))}
                  </ul>
                </div>
                <p className="mt-4 text-xs text-muted-foreground">
                  Die Benutzer können danach neue Container erstellen.
                </p>
              </>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Abbrechen</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            Jetzt löschen
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
