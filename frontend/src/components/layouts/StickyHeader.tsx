import { Menu, Search, Bell } from "lucide-react"

export default function StickyHeader() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/95 px-6 backdrop-blur">
      <button className="md:hidden p-2 -ml-2 text-muted-foreground hover:text-foreground">
        <Menu className="h-5 w-5" />
      </button>
      <div className="flex-1 flex items-center gap-4">
        <div className="relative w-full max-w-sm">
          <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
          <input
            type="search"
            placeholder="Search applications..."
            className="w-full rounded-md border border-input bg-background pl-9 pr-4 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          />
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button className="p-2 text-muted-foreground hover:text-foreground relative">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-destructive"></span>
        </button>
        <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center text-sm font-medium text-primary">
          OP
        </div>
      </div>
    </header>
  )
}
