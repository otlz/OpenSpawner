'use client'

import { usePathname } from 'next/navigation'
import { Separator } from '@/components/ui/separator'
import { SidebarTrigger } from '@/components/ui/sidebar'
import {
  Breadcrumb,
  BreadcrumbList,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'

const BREADCRUMB_LABELS: Record<string, string> = {
  dashboard: 'Dashboard',
  settings: 'Einstellungen',
  admin: 'Admin',
}

export function SiteHeader() {
  const pathname = usePathname()
  const segments = pathname.split('/').filter(Boolean)

  return (
    <header className="flex h-[var(--header-height)] shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear">
      <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mx-2 data-[orientation=vertical]:h-4"
        />
        <Breadcrumb>
          <BreadcrumbList>
            {segments.map((segment, index) => {
              const isLast = index === segments.length - 1
              const href = '/' + segments.slice(0, index + 1).join('/')
              const label = BREADCRUMB_LABELS[segment] || segment

              return (
                <span key={href} className="contents">
                  {index > 0 && (
                    <BreadcrumbSeparator className="hidden md:block" />
                  )}
                  <BreadcrumbItem
                    className={!isLast ? 'hidden md:block' : ''}
                  >
                    {isLast ? (
                      <BreadcrumbPage>{label}</BreadcrumbPage>
                    ) : (
                      <BreadcrumbLink href={href}>{label}</BreadcrumbLink>
                    )}
                  </BreadcrumbItem>
                </span>
              )
            })}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
    </header>
  )
}
