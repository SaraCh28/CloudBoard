import React, { useState, useEffect } from "react"
import Dashboard from "./components/Dashboard"
import KanbanBoard from "./components/KanbanBoard"
import Analytics from "./components/Analytics"
import NotificationCenter from "./components/NotificationCenter"
import SettingsRBAC from "./components/SettingsRBAC"
import GlobalSearch from "./components/GlobalSearch"
import { getTasks, createTask, updateTask as apiUpdateTask, deleteTask as apiDeleteTask } from "./lib/api"
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

const initialLogs = [
  { id: 1, type: "system", message: "CloudBoard initialized.", timestamp: "7/6/2026, 4:00 PM" }
]

export default function App() {
  const [tab, setTab] = useState("dashboard")
  const [currentRole, setCurrentRole] = useState("Owner")
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [tasks, setTasks] = useState([])
  const [users, setUsers] = useState(initialUsers)
  const [notificationLogs, setNotificationLogs] = useState(() => {
    const saved = localStorage.getItem("CLOUDBOARD_LOGS")
    return saved ? JSON.parse(saved) : initialLogs
  })
  
  // Fetch tasks from API on mount
  useEffect(() => {
    getTasks()
      .then(data => setTasks(data))
      .catch(err => console.error("Failed to load tasks:", err))
  }, [])

  useEffect(() => {
    localStorage.setItem("CLOUDBOARD_LOGS", JSON.stringify(notificationLogs))
  }, [notificationLogs])

  const addNotificationLog = (type, message) => {
    const log = { id: Date.now(), type, message, timestamp: new Date().toLocaleString() }
    setNotificationLogs(prev => [...prev, log])
  }

  // Task CRUD helpers
  const addTask = async (taskData) => {
    const newId = `PHX-${Math.floor(100 + Math.random() * 900)}`
    const newTask = { id: newId, actualHours: 0, subtasks: [], comments: [], ...taskData }
    
    // Optimistic UI update
    setTasks(prev => [newTask, ...prev])
    addNotificationLog("task_created", `Created new task: ${newId}`)
    
    try {
      await createTask(newTask)
    } catch (err) {
      console.error(err)
      // Rollback would go here in a production app
    }
  }

  const updateTask = async (id, updatedFields) => {
    // Optimistic update
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
    
    try {
      await apiUpdateTask(id, updatedFields)
    } catch (err) {
      console.error(err)
    }
  }

  const deleteTask = async (id) => {
    // Optimistic update
    setTasks(prev => prev.filter(t => t.id !== id))
    addNotificationLog("task_deleted", `Deleted task ${id}`)
    
    try {
      await apiDeleteTask(id)
    } catch (err) {
      console.error(err)
    }
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
            <span className="topbar-title">CloudBoard</span>
            <span style={{ fontSize: "0.75rem", padding: "2px 6px", border: "1px solid var(--border-color)", borderRadius: "10px", color: "var(--text-secondary)" }}>Sprint 12 (Active)</span>
          </div>
          <div className="topbar-actions">
            <GlobalSearch onNavigate={(hit) => {
              if (hit.type === "task") setTab("kanban")
              else if (hit.type === "project") setTab("dashboard")
            }} />
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
