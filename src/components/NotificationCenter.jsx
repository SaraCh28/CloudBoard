import React, { useState, useEffect } from "react";
import { Bell, MessageSquare, AlertCircle, ArrowRight, Play, RefreshCw } from "lucide-react";

export default function NotificationCenter({ notificationLogs }) {
  const [activeStep, setActiveStep] = useState(null); // 'client', 'rabbitmq', 'worker', 'delivery'
  const [simLogs, setSimLogs] = useState([]);
  const [isSimulating, setIsSimulating] = useState(false);

  // Default initial log sequence
  const startSimulation = () => {
    if (isSimulating) return;
    setIsSimulating(true);
    setSimLogs([]);
    setActiveStep("client");
    
    const now = () => new Date().toLocaleTimeString();
    
    // Step 1: Client event triggered
    setTimeout(() => {
      setSimLogs(prev => [
        ...prev, 
        { time: now(), service: "User Service", msg: "Event triggered: User Sara completed task PHX-84 ('Implement JWT Authentication')." }
      ]);
      setActiveStep("rabbitmq");
    }, 1000);

    // Step 2: RabbitMQ exchange publishes event
    setTimeout(() => {
      setSimLogs(prev => [
        ...prev, 
        { time: now(), service: "RabbitMQ Broker", msg: "Publishing event 'task.completed' to exchange 'amq.topic' with routing_key 'tasks.activity'." }
      ]);
    }, 2500);

    // Step 3: Notification Service consumes the event
    setTimeout(() => {
      setActiveStep("worker");
      setSimLogs(prev => [
        ...prev, 
        { time: now(), service: "Notification Service", msg: "Queue worker consumed 'task.completed' event. Resolving organization channels..." }
      ]);
    }, 4000);

    // Step 4: Dispatch notifications to Slack, Email, and In-App
    setTimeout(() => {
      setActiveStep("delivery");
      setSimLogs(prev => [
        ...prev, 
        { time: now(), service: "Notification Service", msg: "Dispatched Slack payload to webhook: Code 200 SUCCESS." },
        { time: now(), service: "Notification Service", msg: "Dispatched AWS SES email notification to owner@company.com: SUCCESS." },
        { time: now(), service: "Notification Service", msg: "Appended in-app notification to member feeds: SUCCESS." }
      ]);
      setIsSimulating(false);
    }, 6000);
  };

  return (
    <div className="notification-view">
      <div className="dashboard-grid">
        {/* Simulator Grid Card */}
        <div className="widget-card span-12">
          <div className="widget-title" style={{ display: "flex", justifyContents: "space-between", alignItems: "center", width: "100%" }}>
            <span>Asynchronous Notification Service Simulator (RabbitMQ Design)</span>
            <button 
              className="btn btn-primary" 
              onClick={startSimulation} 
              disabled={isSimulating}
              style={{ marginLeft: "auto", padding: "6px 12px", fontSize: "0.8rem" }}
            >
              {isSimulating ? (
                <>
                  <RefreshCw size={14} className="animate-spin" /> Simulating...
                </>
              ) : (
                <>
                  <Play size={14} /> Trigger Simulation
                </>
              )}
            </button>
          </div>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
            This panel demonstrates asynchronous message queueing. Instead of sending emails blockingly on the main thread, the App Service publishes an event to RabbitMQ, where a Notification Service processes it in the background.
          </p>

          {/* Interactive Steps Visual */}
          <div className="notif-flow-steps">
            <div className={`notif-step ${activeStep === "client" ? "active" : ""}`}>
              <div style={{ fontSize: "1.25rem" }}>💻</div>
              <span style={{ fontSize: "0.65rem", marginTop: "2px" }}>App Service</span>
              <div className="notif-step-label">Event Fired</div>
            </div>

            <ArrowRight size={16} color="var(--border-color-hover)" />

            <div className={`notif-step ${activeStep === "rabbitmq" ? "active" : ""}`}>
              <div style={{ fontSize: "1.25rem" }}>🐰</div>
              <span style={{ fontSize: "0.65rem", marginTop: "2px" }}>RabbitMQ</span>
              <div className="notif-step-label">Message Broker</div>
            </div>

            <ArrowRight size={16} color="var(--border-color-hover)" />

            <div className={`notif-step ${activeStep === "worker" ? "active" : ""}`}>
              <div style={{ fontSize: "1.25rem" }}>⚙️</div>
              <span style={{ fontSize: "0.65rem", marginTop: "2px" }}>Notif Service</span>
              <div className="notif-step-label">Worker Queue</div>
            </div>

            <ArrowRight size={16} color="var(--border-color-hover)" />

            <div className={`notif-step ${activeStep === "delivery" ? "active" : ""}`}>
              <div style={{ fontSize: "1.25rem" }}>📬</div>
              <span style={{ fontSize: "0.65rem", marginTop: "2px" }}>Delivery</span>
              <div className="notif-step-label">Slack & SES Email</div>
            </div>
          </div>

          {/* Logs */}
          <div className="notif-log" style={{ marginTop: "36px" }}>
            {simLogs.length === 0 ? (
              <div style={{ color: "var(--text-muted)", fontStyle: "italic", textAlign: "center", padding: "10px 0" }}>
                Click 'Trigger Simulation' to watch event queue logs in real-time...
              </div>
            ) : (
              simLogs.map((log, i) => (
                <div key={i} className="notif-log-line">
                  <span className="timestamp">[{log.time}]</span>
                  <span className="highlight">[{log.service}]</span> {log.msg}
                </div>
              ))
            )}
          </div>
        </div>

        {/* Live Notification Feed */}
        <div className="widget-card span-12">
          <div className="widget-title">Live In-App Notification Feed</div>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px", marginTop: "8px" }}>
            {notificationLogs.length === 0 ? (
              <div style={{ padding: "20px", color: "var(--text-muted)", fontSize: "0.85rem", textAlign: "center" }}>
                No notifications logged yet. Switch roles, move tasks, or apply AI suggestions to see logs trigger!
              </div>
            ) : (
              notificationLogs.slice().reverse().map(log => (
                <div key={log.id} style={{ display: "flex", alignItems: "center", gap: "12px", padding: "12px", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", backgroundColor: "var(--bg-tertiary)", fontSize: "0.9rem" }}>
                  <div style={{ width: "8px", height: "8px", borderRadius: "50%", backgroundColor: "var(--accent-gold)" }} />
                  <div>
                    <span style={{ color: "var(--text-secondary)", fontSize: "0.75rem", display: "block" }}>{log.timestamp}</span>
                    <span style={{ color: "var(--text-primary)" }}>{log.message}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
