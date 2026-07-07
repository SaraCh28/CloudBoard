import React, { useState, useEffect } from "react"
import Dashboard from "./components/Dashboard"
import KanbanBoard from "./components/KanbanBoard"
import Analytics from "./components/Analytics"
import NotificationCenter from "./components/NotificationCenter"
import SettingsRBAC from "./components/SettingsRBAC"
import { 
  LayoutDashboard,
  Kanban,
  BarChart3,
  BellRing,
  Settings,
  ShieldAlert,
  Server,
  Menu
} from "lucide-react"

// Robust initial seed data
const initialUsers = [
  { id: "1", name: "Sara", role: "Owner" },
  { id: "2", name: "Ali", role: "Developer" },
  { id: "3", name: "Ahmed", role: "Developer" },
  { id: "4", name: "Fatima", role: "Manager" }
]

const initialTasks = [
  {
    id: "PHX-101",
    title: "Implement JWT Authentication Middleware",
    description: "Create secure authentication endpoints, sign and verify JWT tokens. Save tokens in HTTP-only cookies and implement middleware routing checks.",
    status: "Doing",
    priority: "High",
    assigneeId: "2",
    estimatedHours: 24,
    actualHours: 12,
    labels: ["Backend", "Auth", "Security"],
    subtasks: [
      { id: 1, title: "Create JWT token helpers", isCompleted: true },
      { id: 2, title: "Write express validation middleware", isCompleted: false },
      { id: 3, title: "Setup HTTP-only cookie delivery", isCompleted: false }
    ],
    comments: [
      { id: 1, author: "Sara", content: "Need this to be fully compliant with OWASP guidelines.", created_at: "7/6/2026, 4:10 PM" }
    ]
  },
  {
    id: "PHX-102",
    title: "Fix Login Session Expiration Bug",
    description: "Users report getting randomly logged out when changing tabs. Potentially related to localStorage cache clear triggers.",
    status: "Todo",
    priority: "Urgent",
    assigneeId: "2",
    estimatedHours: 16,
    actualHours: 0,
    labels: ["Bug", "Frontend"],
    subtasks: [
      { id: 1, title: "Isolate tab trigger code", isCompleted: false }
    ],
    comments: []
  },
  {
    id: "PHX-103",
    title: "Design Payment Gateway Schema Migration",
    description: "Design relational schema tables for Stripe customer references, invoices, and payment intents. Must execute zero-downtime migrations.",
    status: "Todo",
    priority: "High",
    assigneeId: "3",
    estimatedHours: 8,
    actualHours: 0,
    labels: ["Database", "Backend"],
    subtasks: [],
    comments: []
  },
  {
    id: "PHX-104",
    title: "Configure Prometheus metrics exporter",
    description: "Expose metrics route `/metrics` in FastAPI application and integrate Prometheus tracking daemon for latency checks.",
    status: "Done",
    priority: "Medium",
    assigneeId: "3",
    estimatedHours: 12,
    actualHours: 14,
    labels: ["Monitoring", "Ops"],
    subtasks: [
      { id: 1, title: "Install prometheus_client library", isCompleted: true },
      { id: 2, title: "Configure mid-level latency recorder", isCompleted: true }
    ],
    comments: []
  },
  {
    id: "PHX-105",
    title: "Refactor User Preference Dashboard Layout",
    description: "Re-align profile panels to fit the new theme system. Clean up legacy CSS utilities.",
    status: "Todo",
    priority: "Low",
    assigneeId: "4",
    estimatedHours: 6,
    actualHours: 0,
    labels: ["Frontend", "UI"],
    subtasks: [],
    comments: []
  }
]

const initialLogs = [
  { id: 1, type: "system", message: "CloudBoard initialized with seed data.", timestamp: "7/6/2026, 4:00 PM" }
]

export default function App() {
  const [tab, setTab] = useState("dashboard")
  const [currentRole, setCurrentRole] = useState("Owner")
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [tasks, setTasks] = useState(() => {
    const saved = localStorage.getItem("CLOUDBOARD_TASKS")
    return saved ? JSON.parse(saved) : initialTasks
  })
  const [users, setUsers] = useState(initialUsers)
  const [notificationLogs, setNotificationLogs] = useState(() => {
    const saved = localStorage.getItem("CLOUDBOARD_LOGS")
    return saved ? JSON.parse(saved) : initialLogs
  })

  // Persist to localStorage
  useEffect(() => {
    localStorage.setItem("CLOUDBOARD_TASKS", JSON.stringify(tasks))
  }, [tasks])

  useEffect(() => {
    localStorage.setItem("CLOUDBOARD_LOGS", JSON.stringify(notificationLogs))
  }, [notificationLogs])

  const addNotificationLog = (type, message) => {
    const log = { id: Date.now(), type, message, timestamp: new Date().toLocaleString() }
    setNotificationLogs(prev => [...prev, log])
  }

  // Task CRUD helpers
  const addTask = (taskData) => {
    const newId = `PHX-${Math.floor(100 + Math.random() * 900)}`
    const newTask = { id: newId, actualHours: 0, subtasks: [], comments: [], ...taskData }
    setTasks(prev => [newTask, ...prev])
    addNotificationLog("task_created", `Created new task: ${newId}`)
  }

  const updateTask = (id, updatedFields) => {
    setTasks(prev => prev.map(t => {
      if (t.id === id) {
        if (updatedFields.status && updatedFields.status !== t.status) {
          addNotificationLog("task_status", `Task ${id} status: ${t.status} → ${updatedFields.status}`)
        }
        if (updatedFields.assigneeId && updatedFields.assigneeId !== t.assigneeId) {
          const name = users.find(u => u.id === updatedFields.assigneeId)?.name || "Unassigned"
          addNotificationLog("task_assignee", `Task ${id} reassigned to ${name}`)
        }
        return { ...t, ...updatedFields }
      }
      return t
    }))
  }

  const deleteTask = (id) => {
    setTasks(prev => prev.filter(t => t.id !== id))
    addNotificationLog("task_deleted", `Deleted task ${id}`)
  }

  return (
    <div className="app-shell">
      {/* Sidebar navigation – collapsible on small screens */}
      <aside className={`sidebar ${sidebarOpen ? "" : "hidden"}`} aria-label="Main navigation">
        <div className="sidebar-header">
          <Server size={20} color="var(--accent-gold)" />
          <span className="logo-text">Cloud<span className="logo-accent">Board</span></span>
        </div>
        <ul className="sidebar-menu">
          <li><div className={`menu-item ${tab === "dashboard" ? "active" : ""}`} onClick={() => setTab("dashboard")}><LayoutDashboard size={18} /><span>Dashboard</span></div></li>
          <li><div className={`menu-item ${tab === "kanban" ? "active" : ""}`} onClick={() => setTab("kanban")}><Kanban size={18} /><span>Kanban Board</span></div></li>
          <li><div className={`menu-item ${tab === "analytics" ? "active" : ""}`} onClick={() => setTab("analytics")}><BarChart3 size={18} /><span>Analytics</span></div></li>
          <li><div className={`menu-item ${tab === "notifications" ? "active" : ""}`} onClick={() => setTab("notifications")}><BellRing size={18} /><span>Notifications</span></div></li>
          <li><div className={`menu-item ${tab === "settings" ? "active" : ""}`} onClick={() => setTab("settings")}><Settings size={18} /><span>Settings & RBAC</span></div></li>
        </ul>
        <div className="sidebar-footer">
          <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem", color: "var(--text-secondary)" }}>
            <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "var(--accent-green)" }} />
            <span>Dev Server Local</span>
          </div>
        </div>
      </aside>

      {/* Main Content wrapper */}
      <div className="main-wrapper">
        <header className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {/* Hamburger for small screens */}
            <button className="btn btn-secondary" aria-label="Toggle navigation" onClick={() => setSidebarOpen(!sidebarOpen)} style={{ display: "flex", alignItems: "center" }}>
              <Menu size={16} />
            </button>
            <span className="topbar-title">RentNGo v2</span>
            <span style={{ fontSize: "0.75rem", padding: "2px 6px", border: "1px solid var(--border-color)", borderRadius: "10px", color: "var(--text-secondary)" }}>Sprint 12 (Active)</span>
          </div>
          <div className="topbar-actions">
            <span style={{ fontSize: "0.8rem", color: "var(--text-secondary)", display: "flex", alignItems: "center", gap: "6px" }}>
              Role: <span className="task-priority-badge priority-low" style={{ margin: 0, textTransform: "uppercase", fontWeight: "700" }}>{currentRole}</span>
            </span>
          </div>
        </header>
        <main className="content-body" role="main">
          {tab === "dashboard" && <Dashboard tasks={tasks} users={users} setTab={setTab} updateTask={updateTask} />}
          {tab === "kanban" && <KanbanBoard tasks={tasks} users={users} addTask={addTask} updateTask={updateTask} deleteTask={deleteTask} currentRole={currentRole} addNotificationLog={addNotificationLog} />}
          {tab === "analytics" && <Analytics tasks={tasks} />}
          {tab === "notifications" && <NotificationCenter notificationLogs={notificationLogs} />}
          {tab === "settings" && <SettingsRBAC currentRole={currentRole} setCurrentRole={setCurrentRole} addNotificationLog={addNotificationLog} />}
        </main>
      </div>
    </div>
  )
}
