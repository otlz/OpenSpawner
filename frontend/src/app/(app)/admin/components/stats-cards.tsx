/** Statistik-Karten für die Admin-Übersicht. */

import { Card, CardContent } from "@/components/ui/card";
import { Users, CheckCircle2, Clock, AlertCircle, ShieldOff } from "lucide-react";

interface Stats {
  total: number;
  active: number;
  verified: number;
  unverified: number;
  blocked: number;
}

export default function StatsCards({ stats }: { stats: Stats }) {
  const items = [
    { icon: Users, value: stats.total, label: "Gesamt", color: "text-muted-foreground" },
    { icon: CheckCircle2, value: stats.active, label: "Aktiv", color: "text-green-500" },
    { icon: Clock, value: stats.verified, label: "Verifiziert", color: "text-blue-500" },
    { icon: AlertCircle, value: stats.unverified, label: "Unverifiziert", color: "text-yellow-500" },
    { icon: ShieldOff, value: stats.blocked, label: "Gesperrt", color: "text-red-500" },
  ];

  return (
    <div className="mb-6 grid gap-4 md:grid-cols-5">
      {items.map(({ icon: Icon, value, label, color }) => (
        <Card key={label}>
          <CardContent className="flex items-center gap-3 p-4">
            <Icon className={`h-8 w-8 ${color}`} />
            <div>
              <p className="text-2xl font-bold">{value}</p>
              <p className="text-xs text-muted-foreground">{label}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
