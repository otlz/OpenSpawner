'use client'

import * as React from 'react'
import { Home, Package, Shield } from 'lucide-react'
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

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const { user } = useAuth()

  const navMain = [
    { title: 'Dashboard', url: '/dashboard', icon: Home },
    ...(user?.is_admin
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
                <Package className="!size-6" />
                <span className="truncate text-sm font-bold">OpenSpawner</span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavMain items={navMain} />
      </SidebarContent>
      <SidebarFooter>
        <NavUser />
      </SidebarFooter>
    </Sidebar>
  )
}
