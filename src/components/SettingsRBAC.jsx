import React, { useState } from "react";
import { Shield, Key, CreditCard, Trash2, Check, AlertTriangle } from "lucide-react";
import { getStoredApiKey, setStoredApiKey } from "../lib/gemini";

export default function SettingsRBAC({ 
  currentRole, 
  setCurrentRole,
  addNotificationLog
}) {
  const [apiKey, setApiKey] = useState(getStoredApiKey());
  const [isSaved, setIsSaved] = useState(false);

  const roles = ["Owner", "Admin", "Manager", "Developer", "Viewer"];

  const handleSaveKey = (e) => {
    e.preventDefault();
    setStoredApiKey(apiKey.trim());
    setIsSaved(true);
    addNotificationLog("settings_updated", `Gemini API key updated in local storage.`);
    setTimeout(() => setIsSaved(false), 3000);
  };

  const handleRoleChange = (role) => {
    setCurrentRole(role);
    addNotificationLog("role_changed", `User role switched to ${role}`);
  };

  // Helper check for permissions
  const canManageBilling = currentRole === "Owner";
  const canDeleteOrg = currentRole === "Owner" || currentRole === "Admin";

  return (
    <div className="settings-view">
      <div className="dashboard-grid">
        {/* Role Selection Widget */}
        <div className="widget-card span-6">
          <div className="widget-title">
            <Shield size={14} color="var(--accent-gold)" /> Role-Based Access Control (RBAC) Switcher
          </div>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
            Select a role to preview platform permissions. CloudBoard dynamically restricts actions such as task deletion, billing changes, or organization removal based on RBAC policies.
          </p>

          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {roles.map(r => (
              <button 
                key={r}
                onClick={() => handleRoleChange(r)}
                className={`btn ${currentRole === r ? "btn-primary" : "btn-secondary"}`}
                style={{ justifyContent: "space-between", textAlign: "left", padding: "12px 16px" }}
              >
                <span>{r}</span>
                {currentRole === r && <Check size={16} />}
              </button>
            ))}
          </div>
        </div>

        {/* Gemini API Key Configuration */}
        <div className="widget-card span-6">
          <div className="widget-title">
            <Key size={14} color="var(--accent-gold)" /> Gemini AI Configuration
          </div>
          <p style={{ fontSize: "0.875rem", color: "var(--text-secondary)", marginBottom: "16px" }}>
            Enter your Google Gemini API Key to enable real-time project estimation, blocker forecasting, and semantic task duplicate analysis. Keys are stored safely in browser LocalStorage.
          </p>

          <form onSubmit={handleSaveKey}>
            <div className="form-group">
              <label className="form-label">Gemini API Key</label>
              <input 
                type="password" 
                className="form-input" 
                placeholder="AIzaSy..." 
                value={apiKey} 
                onChange={(e) => setApiKey(e.target.value)}
              />
            </div>
            
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginTop: "16px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.8rem" }}>
                {getStoredApiKey() ? (
                  <span style={{ color: "var(--accent-green)", fontWeight: "600", display: "flex", alignItems: "center", gap: "4px" }}>
                    <span className="workload-indicator workload-good" style={{ margin: 0 }} /> Real API Active
                  </span>
                ) : (
                  <span style={{ color: "var(--accent-orange)", fontWeight: "600", display: "flex", alignItems: "center", gap: "4px" }}>
                    <AlertTriangle size={12} /> Using Local Mock Fallback
                  </span>
                )}
              </div>
              
              <button type="submit" className="btn btn-primary" style={{ padding: "8px 16px" }}>
                {isSaved ? "Saved!" : "Save Key"}
              </button>
            </div>
          </form>
        </div>

        {/* Restricted Billing Panel */}
        <div className="widget-card span-6">
          <div className="widget-title">
            <CreditCard size={14} /> Organization Billing & Invoices
          </div>
          
          {!canManageBilling ? (
            <div className="rbac-restriction">
              <AlertTriangle size={16} />
              <span>Billing management is restricted. Only Owners can view or modify subscriptions. (Current: {currentRole})</span>
            </div>
          ) : (
            <div>
              <div style={{ padding: "16px", border: "1px solid var(--border-color)", borderRadius: "var(--radius-md)", backgroundColor: "var(--bg-tertiary)" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "8px" }}>
                  <strong>Enterprise Plan</strong>
                  <span style={{ color: "var(--accent-green)" }}>Active</span>
                </div>
                <div style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
                  Next Renewal: August 1, 2026 ($499.00 / month)
                </div>
              </div>
              <button className="btn btn-secondary" style={{ marginTop: "16px", width: "100%" }}>
                Manage Credit Cards
              </button>
            </div>
          )}
        </div>

        {/* Danger Zone / Delete Org */}
        <div className="widget-card span-6">
          <div className="widget-title">
            <Trash2 size={14} color="var(--accent-red)" /> Danger Zone
          </div>
          
          {!canDeleteOrg ? (
            <div className="rbac-restriction">
              <AlertTriangle size={16} />
              <span>Delete organization is restricted. Requires Admin or Owner clearance. (Current: {currentRole})</span>
            </div>
          ) : (
            <div style={{ border: "1px solid var(--accent-red)", padding: "16px", borderRadius: "var(--radius-md)", backgroundColor: "#2d1313" }}>
              <strong style={{ color: "#fca5a5", display: "block", marginBottom: "8px" }}>Delete Organization</strong>
              <p style={{ fontSize: "0.8rem", color: "#fecaca", marginBottom: "16px" }}>
                Permanently deletes the organization, all projects, repositories, boards, and tasks. This operation cannot be undone.
              </p>
              <button 
                className="btn btn-danger" 
                onClick={() => alert("Organization deletion simulated successfully!")}
                style={{ width: "100%" }}
              >
                Delete Organization
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
