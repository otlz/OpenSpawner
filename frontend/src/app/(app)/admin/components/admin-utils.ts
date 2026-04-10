/** Hilfsfunktionen für die Admin-Seite. */

import { AdminUser } from "@/lib/api";

export type StatusColor = "green" | "yellow" | "red";

/** Berechnet die Statusfarbe eines Benutzers basierend auf Aktivität und Status. */
export function getStatusColor(user: AdminUser): StatusColor {
  const now = new Date();
  const lastUsed = user.last_used ? new Date(user.last_used) : null;
  const createdAt = user.created_at ? new Date(user.created_at) : now;
  const referenceDate = lastUsed || createdAt;
  const daysSince = (now.getTime() - referenceDate.getTime()) / (1000 * 60 * 60 * 24);

  switch (user.state) {
    case "registered":
      return daysSince >= 1 ? "red" : "yellow";
    case "verified":
      if (daysSince >= 7) return "red";
      if (daysSince >= 1) return "yellow";
      return "green";
    case "active":
      if (daysSince >= 30) return "red";
      if (daysSince >= 7) return "yellow";
      return "green";
    default:
      return "yellow";
  }
}

/** Gibt die CSS-Klassen für eine Statusfarbe zurück. */
export function getStatusBadgeColor(color: StatusColor) {
  switch (color) {
    case "green":
      return "bg-green-100 text-green-800 border-green-200";
    case "yellow":
      return "bg-yellow-100 text-yellow-800 border-yellow-200";
    case "red":
      return "bg-red-100 text-red-800 border-red-200";
  }
}

/** Übersetzt den internen Status in ein deutsches Label. */
export function getStateLabel(state: string) {
  switch (state) {
    case "registered":
      return "Unverifiziert";
    case "verified":
      return "Verifiziert";
    case "active":
      return "Aktiv";
    default:
      return state;
  }
}

/** Formatiert ein Datum im deutschen Format. */
export function formatDate(dateString: string | null | undefined) {
  if (!dateString) return "-";
  return new Date(dateString).toLocaleDateString("de-DE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
