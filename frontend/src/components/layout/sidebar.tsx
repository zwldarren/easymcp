"use client";

import React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Home, Settings, Activity, FileText, Key } from "lucide-react";
import { McpIcon } from "@/components/common/mcp-icon";
import { EasyMcpIcon } from "@/components/common/easymcp-icon";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/hooks/use-auth";
import { LogOut } from "lucide-react";

interface SidebarProps {
  className?: string;
}

interface NavItem {
  title: string;
  icon: React.ComponentType<{ className?: string }>;
  href?: string;
  badge?: string;
  children?: NavItem[];
}

const navItems: NavItem[] = [
  {
    title: "Dashboard",
    icon: Home,
    href: "/",
  },
  {
    title: "Servers",
    icon: McpIcon,
    href: "/app/servers",
  },
  {
    title: "System Status",
    icon: Activity,
    href: "/app/status",
  },
];

const settingsItems: NavItem[] = [
  {
    title: "General",
    icon: Settings,
    href: "/app/settings/general",
  },
  {
    title: "API Keys",
    icon: Key,
    href: "/app/settings/api-keys",
  },
  {
    title: "Documentation",
    icon: FileText,
    href: "/app/docs",
  },
];

export function Sidebar({ className }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  const NavItemComponent = ({
    item,
    level = 0,
  }: {
    item: NavItem;
    level?: number;
  }) => {
    const isActive = item.href === pathname;

    return (
      <Link href={item.href!}>
        <Button
          variant="ghost"
          className={cn("nav-item", isActive && "active", level > 0 && "ml-4")}
        >
          <item.icon className="mr-3 h-4 w-4" />
          <span className="flex-1 text-left">{item.title}</span>
          {item.badge && (
            <Badge variant="secondary" className="ml-auto text-xs">
              {item.badge}
            </Badge>
          )}
        </Button>
      </Link>
    );
  };

  return (
    <aside
      className={cn(
        "bg-background/95 supports-[backdrop-filter]:bg-background/60 w-64 border-r backdrop-blur",
        "fixed flex h-screen flex-col",
        className
      )}
    >
      {/* Logo Section */}
      <div className="border-b p-6">
        <div className="flex items-center space-x-3">
          <div className="icon-container">
            <EasyMcpIcon className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">EasyMCP</h2>
            <p className="text-muted-foreground text-xs">MCP Proxy Server</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-2 p-4">
        <div className="space-y-1">
          {navItems.map((item) => (
            <NavItemComponent key={item.title} item={item} />
          ))}
        </div>

        <Separator className="my-4" />

        <div className="space-y-1">
          <p className="text-muted-foreground px-3 py-2 text-xs font-medium">
            Settings
          </p>
          {settingsItems.map((item) => (
            <NavItemComponent key={item.title} item={item} />
          ))}
        </div>
      </nav>

      {/* User Info */}
      <div className="border-t p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary/10 text-primary font-medium">
                {user?.username?.charAt(0).toUpperCase() || "U"}
              </AvatarFallback>
            </Avatar>
            <div className="text-sm">
              <div className="font-medium">{user?.username || "User"}</div>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={logout}
            className="text-muted-foreground hover:text-foreground h-8 px-2"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
