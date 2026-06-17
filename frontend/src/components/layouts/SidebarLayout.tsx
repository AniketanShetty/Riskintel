import { Outlet, Link, useLocation } from "react-router-dom"
import { Activity, FileText, Inbox, BarChart3, Settings, Terminal } from "lucide-react"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Dashboard", href: "/", icon: BarChart3 },
  { name: "Loan Journey", href: "/journey", icon: Terminal },
  { name: "Applications", href: "/applications", icon: FileText },
  { name: "Intake Form", href: "/apply", icon: Inbox },
  { name: "Dead Letter Queue", href: "/dlq", icon: Activity },
  { name: "Settings", href: "/settings", icon: Settings },
]

export default function SidebarLayout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background flex">
      {/* Sidebar */}
      <div className="w-64 border-r border-border bg-secondary/30 flex flex-col hidden md:flex">
        <div className="h-16 flex items-center px-6 border-b border-border">
          <div className="font-bold text-xl tracking-tight text-primary flex items-center gap-2">
            <Activity className="h-6 w-6 text-blue-600" />
            RiskIntel V2
          </div>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = location.pathname === item.href || (item.href !== "/" && location.pathname.startsWith(item.href))
            return (
              <Link
                key={item.name}
                to={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-secondary hover:text-secondary-foreground"
                )}
              >
                <item.icon className="h-5 w-5" />
                {item.name}
              </Link>
            )
          })}
        </nav>
        <div className="p-4 border-t border-border">
          <div className="text-xs text-muted-foreground text-center">v2.0.0-rc1</div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        <Outlet />
      </div>
    </div>
  )
}
