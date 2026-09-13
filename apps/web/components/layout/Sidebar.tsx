"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  BookOpen,
  ChevronDown,
  FlaskConical,
  Github,
  Key,
  LayoutDashboard,
  ListChecks,
  LogOut,
  Settings,
  Sparkles,
  User,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import { useToast } from "@/components/ui/toast";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface SidebarProps {
  projectId: string;
  projectName: string;
}

interface NavItem {
  label: string;
  href: string;
  icon: React.ReactNode;
  comingSoon?: boolean;
}

function NavLink({
  item,
  isActive,
}: {
  item: NavItem;
  isActive: boolean;
}) {
  const inner = (
    <div
      className={cn(
        "flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm transition-colors",
        isActive
          ? "bg-accent text-accent-foreground font-medium"
          : "text-muted-foreground hover:text-foreground hover:bg-accent/50",
        item.comingSoon && "opacity-50 cursor-not-allowed"
      )}
    >
      {item.icon}
      <span>{item.label}</span>
      {item.comingSoon && (
        <span className="ml-auto text-[10px] font-medium text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
          Soon
        </span>
      )}
    </div>
  );

  if (item.comingSoon) {
    return (
      <Tooltip>
        <TooltipTrigger>
          <div>{inner}</div>
        </TooltipTrigger>
        <TooltipContent side="right">Coming soon</TooltipContent>
      </Tooltip>
    );
  }

  return <Link href={item.href}>{inner}</Link>;
}

export function Sidebar({ projectId, projectName }: SidebarProps) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const base = `/projects/${projectId}`;

  const handleLogout = () => {
    logout();
    toast({
      title: "Signed out",
      description: "You have been successfully signed out.",
      variant: "success",
    });
  };

  const navItems: NavItem[] = [
    {
      label: "Overview",
      href: base,
      icon: <LayoutDashboard className="h-4 w-4" />,
    },
    {
      label: "Traces",
      href: `${base}/traces`,
      icon: <Activity className="h-4 w-4" />,
    },
    {
      label: "Playground",
      href: `${base}/playground`,
      icon: <FlaskConical className="h-4 w-4" />,
      comingSoon: true,
    },
    {
      label: "Evaluations",
      href: `${base}/evaluations`,
      icon: <ListChecks className="h-4 w-4" />,
      comingSoon: true,
    },
  ];

  const settingsItems: NavItem[] = [
    {
      label: "Settings",
      href: `${base}/settings`,
      icon: <Settings className="h-4 w-4" />,
    },
    {
      label: "API Keys",
      href: `${base}/settings/api-keys`,
      icon: <Key className="h-4 w-4" />,
    },
  ];

  return (
    <aside className="hidden md:flex h-screen w-56 shrink-0 flex-col border-r border-border bg-sidebar">
      {/* Logo */}
      <div className="flex items-center gap-2 px-4 py-4">
        <div className="flex h-6 w-6 items-center justify-center rounded bg-primary">
          <Sparkles className="h-3.5 w-3.5 text-primary-foreground" />
        </div>
        <span className="text-sm font-semibold tracking-tight text-foreground">
          RAGLens
        </span>
      </div>

      <Separator />

      {/* Project selector */}
      <div className="px-3 pt-3 pb-1">
        <p className="mb-1 px-2.5 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Project
        </p>
        <Link href="/projects" aria-label="Switch project" className="flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-sm font-medium text-foreground hover:bg-accent/50 transition-colors">
          <span className="truncate">{projectName}</span>
          <ChevronDown className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
        </Link>
      </div>

      <Separator className="my-2" />

      {/* Main nav */}
      <nav className="flex-1 px-3 space-y-0.5 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            isActive={
              item.href === base
                ? pathname === base
                : pathname.startsWith(item.href)
            }
          />
        ))}

        <Separator className="my-2" />

        {settingsItems.map((item) => (
          <NavLink
            key={item.href}
            item={item}
            isActive={pathname === item.href}
          />
        ))}
      </nav>

      {/* Footer links */}
      <div className="px-3 pb-4 space-y-0.5">
        <Separator className="mb-2" />
        
        {/* User info */}
        {user && (
          <div className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 mb-2 bg-muted/50">
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 shrink-0">
              <User className="h-3.5 w-3.5 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-foreground truncate">
                {user.full_name || user.email.split("@")[0]}
              </p>
              <p className="text-[10px] text-muted-foreground truncate">
                {user.email}
              </p>
            </div>
          </div>
        )}

        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>

        <Separator className="my-2" />
        
        <a
          href="/docs"
          className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 text-sm text-muted-foreground hover:text-foreground hover:bg-accent/50 transition-colors"
        >
          <BookOpen className="h-4 w-4" />
          Documentation
        </a>
      </div>
    </aside>
  );
}
