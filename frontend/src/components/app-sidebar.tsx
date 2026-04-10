'use client'

import * as React from 'react'
import { Github, Home, PackageOpen, Shield } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import Link from 'next/link'

import { NavMain } from '@/components/nav-main'
import { NavUser } from '@/components/nav-user'
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar'
import { Skeleton } from '@/components/ui/skeleton'

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { user, isLoading } = useAuth()

  const navMain = [
    { title: 'Dashboard', url: '/dashboard', icon: Home },
    ...(user?.role === 'admin' || user?.role === 'manager'
      ? [{ title: 'Admin', url: '/admin', icon: Shield }]
      : []),
  ]

  return (
    <Sidebar variant="inset" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link href="/dashboard">
                <PackageOpen className="!size-6" />
                <span className="truncate text-xl font-bold">OpenSpawner</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        {isLoading ? (
          <div className="p-3 space-y-2">
            <Skeleton className="h-8 w-full rounded-md" />
            <Skeleton className="h-8 w-full rounded-md" />
          </div>
        ) : (
          <NavMain items={navMain} />
        )}
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <a href="https://github.com/otlz/OpenSpawner" target="_blank" rel="noopener noreferrer">
                <Github className="size-4" />
                <span>GitHub</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
        {isLoading ? (
          <div className="flex items-center gap-2 p-2">
            <Skeleton className="h-8 w-8 rounded-lg" />
            <div className="flex-1 space-y-1">
              <Skeleton className="h-3.5 w-32" />
              <Skeleton className="h-3 w-20" />
            </div>
          </div>
        ) : (
          <NavUser />
        )}
      </SidebarFooter>
    </Sidebar>
  )
}
