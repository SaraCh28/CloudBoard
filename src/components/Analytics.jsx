import React from "react";
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend,
  AreaChart,
  Area
} from "recharts";
import { Calendar, Activity, BarChart2, CheckCircle2 } from "lucide-react";

export default function Analytics({ tasks }) {
  // Compute chart metrics dynamically or seed them with realistic progression
  const totalTasks = tasks.length;
  const completedCount = tasks.filter(t => t.status === "Done").length;
  
  // Velocity Chart Data (Completed tasks per sprint)
  const velocityData = [
    { name: "Sprint 8", completed: 18, planned: 20 },
    { name: "Sprint 9", completed: 22, planned: 24 },
    { name: "Sprint 10", completed: 15, planned: 22 },
    { name: "Sprint 11", completed: 25, planned: 26 },
    { name: "Sprint 12 (Current)", completed: completedCount, planned: totalTasks }
  ];

  // Bug Trend Data
  const bugTrendData = [
    { name: "Week 1", open: 12, resolved: 8 },
    { name: "Week 2", open: 15, resolved: 14 },
    { name: "Week 3", open: 8, resolved: 12 },
    { name: "Week 4", open: 18, resolved: 9 },
    { name: "Week 5", open: 10, resolved: 15 },
    { name: "Week 6", open: 6, resolved: 11 }
  ];

  // Cycle Time Data (Completion Time in Days)
  const cycleTimeData = [
    { priority: "Low", days: 1.2 },
    { priority: "Medium", days: 2.1 },
    { priority: "High", days: 3.4 },
    { priority: "Urgent", days: 0.8 }
  ];

  // Calculate some insights
  const avgCompletionTime = "2.3 days";
  const velocity = 21.4; // avg completed tasks per sprint

  return (
    <div className="analytics-view">
      {/* Metrics Row */}
      <div className="dashboard-grid" style={{ marginBottom: "24px" }}>
        <div className="widget-card span-3">
          <div className="widget-title">
            <CheckCircle2 size={14} color="var(--accent-green)" /> Velocity Average
          </div>
          <div className="widget-value" style={{ color: "var(--accent-green)" }}>{velocity}</div>
          <div className="widget-sub">Completed tasks per sprint</div>
        </div>

        <div className="widget-card span-3">
          <div className="widget-title">
            <Activity size={14} color="var(--accent-gold)" /> Cycle Time
          </div>
          <div className="widget-value" style={{ color: "var(--accent-gold)" }}>{avgCompletionTime}</div>
          <div className="widget-sub">Average time to close task</div>
        </div>

        <div className="widget-card span-3">
          <div className="widget-title">
            <Calendar size={14} color="var(--accent-blue)" /> Sprint Status
          </div>
          <div className="widget-value" style={{ color: "var(--accent-blue)" }}>Day 8</div>
          <div className="widget-sub">4 days remaining in Sprint 12</div>
        </div>

        <div className="widget-card span-3">
          <div className="widget-title">
            <BarChart2 size={14} /> Total Completed
          </div>
          <div className="widget-value">{completedCount} / {totalTasks}</div>
          <div className="widget-sub">Active tasks: {totalTasks - completedCount}</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="dashboard-grid">
        {/* Sprint Velocity */}
        <div className="widget-card span-6">
          <div className="widget-title">Sprint Velocity (Completed vs Planned)</div>
          <div style={{ width: "100%", height: 300, marginTop: "16px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={velocityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={11} />
                <YAxis stroke="var(--text-secondary)" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                <Bar dataKey="completed" fill="var(--accent-green)" name="Completed Tasks" radius={[4, 4, 0, 0]} />
                <Bar dataKey="planned" fill="var(--border-color-hover)" name="Planned Tasks" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Bug Trends */}
        <div className="widget-card span-6">
          <div className="widget-title">Bug Tracking Trends (Active vs Resolved)</div>
          <div style={{ width: "100%", height: 300, marginTop: "16px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={bugTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="name" stroke="var(--text-secondary)" fontSize={11} />
                <YAxis stroke="var(--text-secondary)" fontSize={11} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}
                />
                <Legend wrapperStyle={{ fontSize: 12, paddingTop: 10 }} />
                <Line type="monotone" dataKey="open" stroke="var(--accent-red)" strokeWidth={2} name="Bugs Opened" />
                <Line type="monotone" dataKey="resolved" stroke="var(--accent-green)" strokeWidth={2} name="Bugs Resolved" />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Cycle Time Area Chart */}
        <div className="widget-card span-12">
          <div className="widget-title">Task Cycle Time by Priority</div>
          <div style={{ width: "100%", height: 260, marginTop: "16px" }}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={cycleTimeData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorDays" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="var(--accent-gold)" stopOpacity={0.4}/>
                    <stop offset="95%" stopColor="var(--accent-gold)" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                <XAxis dataKey="priority" stroke="var(--text-secondary)" fontSize={11} />
                <YAxis stroke="var(--text-secondary)" fontSize={11} label={{ value: 'Days', angle: -90, position: 'insideLeft', fill: 'var(--text-secondary)', fontSize: 11 }} />
                <Tooltip 
                  contentStyle={{ backgroundColor: "var(--bg-secondary)", borderColor: "var(--border-color)", color: "var(--text-primary)" }}
                />
                <Area type="monotone" dataKey="days" stroke="var(--accent-gold)" fillOpacity={1} fill="url(#colorDays)" strokeWidth={2} name="Avg Resolution Days" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
