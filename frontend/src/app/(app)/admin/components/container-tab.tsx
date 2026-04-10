/** Container-Verwaltungs-Tab für die Admin-Seite. */

import { AdminUser } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Container,
  Shield,
  ShieldOff,
  RefreshCw,
  Loader2,
  Search,
} from "lucide-react";

interface ContainerTabProps {
  users: AdminUser[];
  searchTerm: string;
  onSearchChange: (term: string) => void;
  selectedContainerIds: Set<number>;
  onToggleSelection: (id: number) => void;
  onClearSelection: () => void;
  actionLoading: number | null;
  onBlockContainer: (id: number, type: string) => void;
  onUnblockContainer: (id: number, type: string) => void;
  onBulkBlock: () => void;
  onBulkUnblock: () => void;
  onRefresh: () => void;
}

export default function ContainerTab({
  users,
  searchTerm,
  onSearchChange,
  selectedContainerIds,
  onToggleSelection,
  onClearSelection,
  actionLoading,
  onBlockContainer,
  onUnblockContainer,
  onBulkBlock,
  onBulkUnblock,
  onRefresh,
}: ContainerTabProps) {
  const totalContainers = users.reduce((sum, u) => sum + (u.containers?.length || 0), 0);

  return (
    <>
      {/* Bulk-Action Bar */}
      {selectedContainerIds.size > 0 && (
        <div className="mb-4 rounded-lg border border-primary bg-primary/5 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="font-medium">
                {selectedContainerIds.size} Container ausgewählt
              </span>
              <Button variant="outline" size="sm" onClick={onClearSelection} className="text-xs">
                Auswahl aufheben
              </Button>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={onBulkBlock} disabled={actionLoading !== null}>
                <ShieldOff className="mr-2 h-4 w-4" />
                Sperren
              </Button>
              <Button variant="outline" size="sm" onClick={onBulkUnblock} disabled={actionLoading !== null}>
                <Shield className="mr-2 h-4 w-4" />
                Entsperren
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Suche */}
      <div className="mb-6 flex items-center gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Container oder User suchen..."
            value={searchTerm}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button variant="outline" onClick={onRefresh}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Aktualisieren
        </Button>
      </div>

      {/* Container Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {users.flatMap((u) =>
          (u.containers || [])
            .filter(
              (container) =>
                u.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
                container.container_type.toLowerCase().includes(searchTerm.toLowerCase())
            )
            .map((container) => (
              <Card
                key={container.id}
                className={`relative overflow-hidden transition-all ${
                  container.is_blocked ? "border-red-500 bg-red-50" : ""
                } ${selectedContainerIds.has(container.id) ? "border-primary bg-primary/5" : ""}`}
              >
                {/* Checkbox */}
                <div className="absolute top-2 left-2">
                  <input
                    type="checkbox"
                    checked={selectedContainerIds.has(container.id)}
                    onChange={() => onToggleSelection(container.id)}
                    className="h-4 w-4 rounded border-gray-300"
                  />
                </div>

                {/* Gesperrt-Badge */}
                {container.is_blocked && (
                  <div className="absolute top-2 right-2">
                    <Badge variant="destructive" className="text-xs">Gesperrt</Badge>
                  </div>
                )}

                <CardHeader className="pt-10">
                  <CardTitle className="text-lg">{container.container_type}</CardTitle>
                  <CardDescription className="text-sm">User: {u.email}</CardDescription>
                </CardHeader>

                <CardContent className="space-y-3">
                  <div className="space-y-1 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Status:</span>
                      <span className="font-medium">
                        {container.container_id ? "Läuft" : "Gestoppt"}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Erstellt:</span>
                      <span className="font-mono text-xs">
                        {container.created_at
                          ? new Date(container.created_at).toLocaleDateString("de-DE")
                          : "-"}
                      </span>
                    </div>
                    {container.is_blocked && container.blocked_at && (
                      <div className="flex justify-between text-destructive">
                        <span className="text-muted-foreground">Gesperrt:</span>
                        <span className="font-mono text-xs">
                          {new Date(container.blocked_at).toLocaleString("de-DE")}
                        </span>
                      </div>
                    )}
                  </div>

                  {/* Aktions-Buttons */}
                  <div className="flex gap-2 pt-2">
                    {container.is_blocked ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onUnblockContainer(container.id, container.container_type)}
                        disabled={actionLoading === container.id}
                        className="flex-1 text-xs"
                      >
                        {actionLoading === container.id ? (
                          <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                        ) : (
                          <Shield className="mr-2 h-3 w-3" />
                        )}
                        Entsperren
                      </Button>
                    ) : (
                      <Button
                        size="sm"
                        variant="destructive"
                        onClick={() => onBlockContainer(container.id, container.container_type)}
                        disabled={actionLoading === container.id}
                        className="flex-1 text-xs"
                      >
                        {actionLoading === container.id ? (
                          <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                        ) : (
                          <ShieldOff className="mr-2 h-3 w-3" />
                        )}
                        Sperren
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
        )}
      </div>

      {totalContainers === 0 && (
        <div className="py-12 text-center text-muted-foreground">
          Keine Container gefunden
        </div>
      )}
    </>
  );
}
