import { SiNginx, SiNextdotjs, SiVscodium, SiSqlite, SiPlatformio } from "react-icons/si";
import { Container as ContainerIcon } from "lucide-react";
import type { IconType } from "react-icons";

const iconMap: Record<string, IconType> = {
  SiNginx,
  SiNextdotjs,
  SiVisualstudiocode: SiVscodium,
  SiSqlite,
  SiPlatformio,
};

export function getContainerIcon(iconName?: string, className = "h-6 w-6") {
  if (!iconName || !iconMap[iconName]) {
    return <ContainerIcon className={className} />;
  }
  const Icon = iconMap[iconName];
  return <Icon className={className} />;
}
