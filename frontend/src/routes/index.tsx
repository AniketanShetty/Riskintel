import { createBrowserRouter } from "react-router-dom"
import SidebarLayout from "@/components/layouts/SidebarLayout"
import StickyHeader from "@/components/layouts/StickyHeader"
import ApplicationDetail from "@/features/applications/ApplicationDetail"
import ApplyForm from "@/features/applications/ApplyForm"
import ApplicationList from "@/features/applications/ApplicationList"
import Dashboard from "@/features/dashboard/Dashboard"
import DeadLetterQueue from "@/features/dlq/DeadLetterQueue"
import LoanJourneyConsole from "@/features/journey/LoanJourneyConsole"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <SidebarLayout />,
    children: [
      {
        index: true,
        element: (
          <>
            <StickyHeader />
            <main className="p-6">
              <Dashboard />
            </main>
          </>
        ),
      },
      {
        path: "journey",
        element: <LoanJourneyConsole />,
      },
      {
        path: "journey/:sessionId",
        element: <LoanJourneyConsole />,
      },
      {
        path: "applications/:id",
        element: (
          <>
            <StickyHeader />
            <ApplicationDetail />
          </>
        ),
      },
      {
        path: "apply",
        element: (
          <>
            <StickyHeader />
            <main className="p-6">
              <ApplyForm />
            </main>
          </>
        ),
      },
      {
        path: "dlq",
        element: (
          <>
            <StickyHeader />
            <main className="p-6">
              <DeadLetterQueue />
            </main>
          </>
        ),
      },
      {
        path: "applications",
        element: (
          <>
            <StickyHeader />
            <main className="p-6">
              <ApplicationList />
            </main>
          </>
        ),
      },
      {
        path: "settings",
        element: (
          <>
            <StickyHeader />
            <main className="p-6">
              <h1 className="text-2xl font-bold mb-4">Settings Placeholder</h1>
            </main>
          </>
        ),
      },
    ],
  },
])
