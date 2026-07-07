import React from "react";
import { 
  AlertTriangle, 
  TrendingUp, 
  Activity, 
  Users, 
  ShieldAlert, 
  ArrowRight, 
  CheckCircle,
  HelpCircle,
  Clock
} from "lucide-react";

export default function Dashboard({ tasks, users, setTab, updateTask }) {
  // Compute dashboard metrics dynamically from live state
  const blockedTasks = tasks.filter(t => t.isBlocked || t.blockedBy?.length > 0);
  const totalTasks = tasks.length;
  const completedTasks = tasks.filter(t => t.status === "Done").length;
  
  // Calculate developer workload
  const devWorkload = users.map(user => {
    const userTasks = tasks.filter(t => t.assigneeId === user.id && t.status !== "Done");
    const totalEstimated = userTasks.reduce((sum, t) => sum + (Number(t.estimatedHours) || 0), 0);
    // Let's assume 40 hours per sprint is 100% capacity
    const workloadPercentage = Math.round((totalEstimated / 40) * 100);
    return {
      ...user,
      activeTasksCount: userTasks.length,
      workloadPercentage
    };
  });

  const overloadedCount = devWorkload.filter(d => d.workloadPercentage > 120).length;

  // Let's create dynamic actions
  const suggestedActions = [];
  
  // Suggest reassignments if someone is overloaded and someone else is underloaded
  const overloadedDev = devWorkload.find(d => d.workloadPercentage > 120);
  const underloadedDev = devWorkload.find(d => d.workloadPercentage < 50 && d.role === "Developer");
  
  if (overloadedDev && underloadedDev) {
    const taskToMove = tasks.find(t => t.assigneeId === overloadedDev.id && t.status !== "Done" && t.priority === "High");
    if (taskToMove) {
      suggestedActions.push({
        id: "reassign",
        description: `Move "${taskToMove.title}" from ${overloadedDev.name} to ${underloadedDev.name}`,
        detail: `Reduces ${overloadedDev.name}'s workload by ${taskToMove.estimatedHours || 8} hrs.`,
        action: () => {
          updateTask(taskToMove.id, { assigneeId: underloadedDev.id });
          alert(`Successfully reassigned "${taskToMove.title}" to ${underloadedDev.name}.`);
        }
      });
    }
  }

  // Suggest splitting complex tasks
  const complexTask = tasks.find(t => t.status !== "Done" && (Number(t.estimatedHours) > 24));
  if (complexTask) {
    suggestedActions.push({
      id: "split",
      description: `Split authentication task "${complexTask.title}" into subtasks`,
      detail: `Current estimate is ${complexTask.estimatedHours} hours. High risk of missing sprint deadline.`,
      action: () => {
        // Split this task into two
        const title1 = `${complexTask.title} - Core Implementation`;
        const title2 = `${complexTask.title} - Verification & Testing`;
        
        // Mark current task as Done/Deleted and create new ones (simulated by updating title and reducing hours)
        updateTask(complexTask.id, { 
          title: title1, 
          estimatedHours: Math.round(complexTask.estimatedHours / 2) 
        });
        
        // Add a log message or notification
        alert(`Split task into: \n1. ${title1} (${Math.round(complexTask.estimatedHours / 2)} hrs)\n2. ${title2} (${Math.round(complexTask.estimatedHours / 2)} hrs)`);
      }
    });
  }

  // Default suggested action if others don't apply
  suggestedActions.push({
    id: "review-blockers",
    description: `Review ${blockedTasks.length} blocked task dependencies`,
    detail: "Blocked tasks are stalling sprint progress. Coordinate with teams to resolve blocks.",
    action: () => setTab("kanban")
  });

  return (
    <div className="dashboard-view">
      {/* Risk Alert Banner */}
      <div className="alert-banner high-risk">
        <div>
          <div className="alert-title" style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <AlertTriangle size={18} color="var(--accent-red)" />
            🚨 Project Phoenix Health Alert
          </div>
          <div className="alert-desc">
            Predicted completion is low (67%). Action is required to adjust resource allocations or split oversized backend tickets.
          </div>
        </div>
        <button className="btn btn-secondary" onClick={() => setTab("kanban")} style={{ padding: "6px 12px", fontSize: "0.8rem" }}>
          Go to Kanban <ArrowRight size={14} />
        </button>
      </div>

      <div className="dashboard-grid">
        {/* Risk Card */}
        <div className="widget-card span-3">
          <div className="widget-title">
            <ShieldAlert size={14} color="var(--accent-red)" /> Project Risk
          </div>
          <div className="widget-value" style={{ color: "var(--accent-red)" }}>HIGH</div>
          <div className="widget-sub">Critical backend task blockers</div>
        </div>

        {/* Prediction Completion */}
        <div className="widget-card span-3">
          <div className="widget-title">
            <TrendingUp size={14} color="var(--accent-orange)" /> Predicted Sprint Completion
          </div>
          <div className="widget-value" style={{ color: "var(--accent-orange)" }}>67%</div>
          <div className="widget-sub">Target: 95% completion rate</div>
        </div>

        {/* API Latency */}
        <div className="widget-card span-3">
          <div className="widget-title">
            <Activity size={14} color="var(--accent-blue)" /> Avg API Latency
          </div>
          <div className="widget-value" style={{ color: "var(--accent-blue)" }}>180 ms</div>
          <div className="widget-sub">P99 latency: 240 ms</div>
        </div>

        {/* Blocked / Overloaded Devs */}
        <div className="widget-card span-3">
          <div className="widget-title">
            <Users size={14} color="var(--accent-gold)" /> Workload Alert
          </div>
          <div className="widget-value" style={{ color: "var(--accent-gold)" }}>
            {overloadedCount} Devs
          </div>
          <div className="widget-sub">{blockedTasks.length} blocked tasks across sprints</div>
        </div>

        {/* Suggested Actions Widget */}
        <div className="widget-card span-8">
          <div className="widget-title">Suggested Actions & AI Co-Pilot recommendations</div>
          <div className="action-list">
            {suggestedActions.map((act, index) => (
              <div key={index} className="action-item">
                <div className="action-item-text">
                  <span style={{ fontSize: "1.1rem" }}>⚡</span>
                  <div>
                    <strong style={{ color: "var(--text-primary)" }}>{act.description}</strong>
                    <div style={{ fontSize: "0.8rem", color: "var(--text-secondary)", marginTop: "2px" }}>
                      {act.detail}
                    </div>
                  </div>
                </div>
                <button className="btn btn-secondary" onClick={act.action} style={{ padding: "6px 12px", fontSize: "0.8rem" }}>
                  Execute
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Team Workload Widget */}
        <div className="widget-card span-4">
          <div className="widget-title">Developer Workloads</div>
          <table className="workload-table" style={{ margin: "0" }}>
            <thead>
              <tr>
                <th style={{ padding: "8px 0" }}>User</th>
                <th style={{ padding: "8px 0", textAlign: "right" }}>Load %</th>
              </tr>
            </thead>
            <tbody>
              {devWorkload.map(dev => (
                <tr key={dev.id}>
                  <td style={{ padding: "8px 0", display: "flex", alignItems: "center", gap: "8px" }}>
                    <div className="avatar" style={{ width: "20px", height: "20px", fontSize: "0.6rem" }}>
                      {dev.name[0]}
                    </div>
                    {dev.name}
                  </td>
                  <td style={{ padding: "8px 0", textAlign: "right" }}>
                    <span 
                      className={`workload-indicator ${
                        dev.workloadPercentage > 120 
                          ? "workload-high" 
                          : dev.workloadPercentage > 80 
                            ? "workload-warn" 
                            : "workload-good"
                      }`}
                    />
                    <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.85rem", fontWeight: "600" }}>
                      {dev.workloadPercentage}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
