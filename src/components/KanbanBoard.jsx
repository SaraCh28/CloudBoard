import React, { useState, useEffect } from "react";
import { 
  Plus, 
  Search, 
  MessageSquare, 
  CheckSquare, 
  Calendar, 
  Clock, 
  Sparkles, 
  AlertTriangle,
  User, 
  CornerDownRight, 
  HelpCircle,
  X,
  PlusCircle,
  ArrowRight,
  TrendingDown
} from "lucide-react";
import { getAiTaskEstimation, getAiDuplicateCheck } from "../lib/gemini";

export default function KanbanBoard({ 
  tasks, 
  users, 
  addTask, 
  updateTask, 
  deleteTask, 
  currentRole,
  addNotificationLog
}) {
  const [selectedTask, setSelectedTask] = useState(null);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  
  // Create New Task Form State
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newPriority, setNewPriority] = useState("Medium");
  const [newAssignee, setNewAssignee] = useState(users[0]?.id || "");
  const [newEstHours, setNewEstHours] = useState(8);
  const [newLabels, setNewLabels] = useState("Feature");
  
  // AI State
  const [aiLoading, setAiLoading] = useState(false);
  const [aiResult, setAiResult] = useState(null);
  const [dupResult, setDupResult] = useState(null);
  
  // Detail Modal State
  const [newComment, setNewComment] = useState("");
  const [newSubtask, setNewSubtask] = useState("");

  // Search filter
  const filteredTasks = tasks.filter(t => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) return true;
    
    // Support advanced search: e.g. "high priority backend bugs assigned to Sara"
    const priorityMatch = query.includes("high") && t.priority === "High" ||
                          query.includes("urgent") && t.priority === "Urgent" ||
                          query.includes("medium") && t.priority === "Medium" ||
                          query.includes("low") && t.priority === "Low";
                          
    const labelMatch = t.labels?.some(l => query.includes(l.toLowerCase()));
    
    const assignee = users.find(u => u.id === t.assigneeId);
    const assigneeMatch = assignee && query.includes(assignee.name.toLowerCase());
    
    const textMatch = t.title.toLowerCase().includes(query) || 
                      (t.description && t.description.toLowerCase().includes(query));
                      
    return textMatch || priorityMatch || labelMatch || assigneeMatch;
  });

  // Native Drag and Drop handlers
  const handleDragStart = (e, taskId) => {
    e.dataTransfer.setData("taskId", taskId);
  };

  const handleDrop = (e, status) => {
    e.preventDefault();
    const taskId = e.dataTransfer.getData("taskId");
    if (taskId) {
      updateTask(taskId, { status });
      addNotificationLog("task_moved", `Task #${taskId} moved to ${status}`);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  // Perform AI Duplicate check when typing new task title
  useEffect(() => {
    if (newTitle.length > 5) {
      const delayDebounceFn = setTimeout(async () => {
        const check = await getAiDuplicateCheck(newTitle, newDesc, tasks);
        setDupResult(check);
      }, 800);
      return () => clearTimeout(delayDebounceFn);
    } else {
      setDupResult(null);
    }
  }, [newTitle, newDesc]);

  // Request AI Estimation for current task in details
  const handleRequestAiEstimation = async (task) => {
    setAiLoading(true);
    setAiResult(null);
    try {
      const res = await getAiTaskEstimation(task.title, task.description || "", tasks);
      setAiResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setAiLoading(false);
    }
  };

  const applyAiRecommendations = (task) => {
    if (!aiResult) return;
    
    // Add subtasks and update estimated hours
    const updatedSubtasks = [
      ...(task.subtasks || []),
      ...(aiResult.subtasks || []).map((title, idx) => ({
        id: Date.now() + idx,
        title,
        isCompleted: false
      }))
    ];

    const updatedEst = aiResult.estimatedDays ? Math.round(aiResult.estimatedDays * 8) : task.estimatedHours;
    
    updateTask(task.id, {
      subtasks: updatedSubtasks,
      estimatedHours: updatedEst,
      description: task.description + `\n\n[AI Predicted Blockers]:\n` + (aiResult.blockers || []).map(b => `- ${b}`).join("\n")
    });

    // Refresh selectedTask local view
    setSelectedTask({
      ...task,
      subtasks: updatedSubtasks,
      estimatedHours: updatedEst,
      description: task.description + `\n\n[AI Predicted Blockers]:\n` + (aiResult.blockers || []).map(b => `- ${b}`).join("\n")
    });
    
    setAiResult(null);
    alert("AI suggestions applied successfully.");
  };

  const submitAddTask = (e) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    addTask({
      title: newTitle,
      description: newDesc,
      priority: newPriority,
      assigneeId: newAssignee,
      estimatedHours: Number(newEstHours) || 8,
      actualHours: 0,
      labels: newLabels.split(",").map(l => l.trim()).filter(Boolean),
      status: "Todo",
      subtasks: [],
      comments: []
    });

    // Reset Form
    setNewTitle("");
    setNewDesc("");
    setNewPriority("Medium");
    setNewEstHours(8);
    setIsAddOpen(false);
    setDupResult(null);
  };

  // Add Comment to Selected Task
  const handleAddComment = () => {
    if (!newComment.trim() || !selectedTask) return;
    const author = users.find(u => u.role === currentRole)?.name || "Current User";
    
    const commentObj = {
      id: Date.now(),
      author,
      content: newComment,
      created_at: new Date().toLocaleString()
    };

    const updatedComments = [...(selectedTask.comments || []), commentObj];
    updateTask(selectedTask.id, { comments: updatedComments });
    setSelectedTask({ ...selectedTask, comments: updatedComments });
    setNewComment("");
  };

  // Toggle Subtask
  const handleToggleSubtask = (subtaskId) => {
    if (!selectedTask) return;
    const updatedSub = selectedTask.subtasks.map(s => {
      if (s.id === subtaskId) return { ...s, isCompleted: !s.isCompleted };
      return s;
    });
    updateTask(selectedTask.id, { subtasks: updatedSub });
    setSelectedTask({ ...selectedTask, subtasks: updatedSub });
  };

  // Add Subtask manual
  const handleAddSubtask = () => {
    if (!newSubtask.trim() || !selectedTask) return;
    const subObj = {
      id: Date.now(),
      title: newSubtask,
      isCompleted: false
    };
    const updatedSub = [...(selectedTask.subtasks || []), subObj];
    updateTask(selectedTask.id, { subtasks: updatedSub });
    setSelectedTask({ ...selectedTask, subtasks: updatedSub });
    setNewSubtask("");
  };

  // Merge duplicated tasks
  const handleMergeTask = (dupId) => {
    const parentTask = tasks.find(t => t.id === dupId);
    if (!parentTask) return;
    
    alert(`Merged "${newTitle}" into #${parentTask.id} "${parentTask.title}". Added task description as a comment.`);
    
    // Add new description as comment
    const updatedComments = [
      ...(parentTask.comments || []),
      {
        id: Date.now(),
        author: "AI Integrator",
        content: `Merged duplicate request: ${newDesc || 'No desc'}`,
        created_at: new Date().toLocaleString()
      }
    ];
    updateTask(parentTask.id, { comments: updatedComments });
    
    // Reset Add Task Form
    setNewTitle("");
    setNewDesc("");
    setIsAddOpen(false);
    setDupResult(null);
  };

  const getAssigneeName = (id) => {
    return users.find(u => u.id === id)?.name || "Unassigned";
  };

  const columns = ["Todo", "Doing", "Done"];

  return (
    <div className="kanban-container">
      {/* Kanban Sub-Header & Controls */}
      <div className="kanban-header">
        <div style={{ display: "flex", gap: "12px", width: "100%", maxWidth: "450px", position: "relative" }}>
          <Search size={16} style={{ position: "absolute", left: "12px", top: "50%", transform: "translateY(-50%)", color: "var(--text-muted)" }} />
          <input 
            type="text" 
            placeholder="Search by title, description, tags, assignees..." 
            className="form-input"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{ paddingLeft: "36px", width: "100%" }}
          />
        </div>
        
        <button className="btn btn-primary" onClick={() => setIsAddOpen(true)}>
          <Plus size={16} /> Add Task
        </button>
      </div>

      {/* Columns wrapper */}
      <div className="kanban-columns">
        {columns.map(status => {
          const colTasks = filteredTasks.filter(t => t.status === status);
          return (
            <div 
              key={status} 
              className="kanban-column"
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, status)}
            >
              <div className="column-header">
                <div className="column-title">
                  <span>{status === "Todo" ? "📋 Todo" : status === "Doing" ? "⚙️ Doing" : "✅ Done"}</span>
                  <span className="column-count">{colTasks.length}</span>
                </div>
              </div>
              <div className="column-cards">
                {colTasks.length === 0 ? (
                  <div style={{ padding: "30px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.85rem", border: "1px dashed var(--border-color)", borderRadius: "var(--radius-md)" }}>
                    No tasks here
                  </div>
                ) : (
                  colTasks.map(task => (
                    <div 
                      key={task.id} 
                      className="task-card"
                      draggable
                      onDragStart={(e) => handleDragStart(e, task.id)}
                      onClick={() => setSelectedTask(task)}
                    >
                      <div className="task-tags">
                        <span className={`task-priority-badge priority-${task.priority.toLowerCase()}`}>
                          {task.priority}
                        </span>
                        {task.labels?.map(l => (
                          <span key={l} className="task-tag">{l}</span>
                        ))}
                      </div>
                      <div className="task-title">{task.title}</div>
                      
                      {task.subtasks?.length > 0 && (
                        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "8px" }}>
                          <CheckSquare size={12} />
                          {task.subtasks.filter(s => s.isCompleted).length} / {task.subtasks.length} subtasks
                        </div>
                      )}

                      <div className="task-meta">
                        <div className="task-assignee">
                          <div className="avatar">
                            {getAssigneeName(task.assigneeId)[0]}
                          </div>
                          <span>{getAssigneeName(task.assigneeId)}</span>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", gap: "4px" }}>
                          <Clock size={12} />
                          <span>{task.estimatedHours}h</span>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Task Modal */}
      {isAddOpen && (
        <div className="modal-overlay">
          <div className="modal-content">
            <form onSubmit={submitAddTask}>
              <div className="modal-header">
                <h3 className="topbar-title">Create New Task</h3>
                <button type="button" className="btn btn-secondary" onClick={() => setIsAddOpen(false)} style={{ padding: "4px" }}>
                  <X size={16} />
                </button>
              </div>
              <div className="modal-body">
                {dupResult && dupResult.isDuplicate && (
                  <div className="rbac-restriction" style={{ backgroundColor: "#3a2a1c", borderColor: "var(--accent-orange)", color: "#fef3c7", marginBottom: "16px" }}>
                    <AlertTriangle size={18} color="var(--accent-orange)" />
                    <div>
                      <strong>Potential Duplicate Task Detected ({dupResult.similarityPercentage}%)</strong>
                      <div style={{ fontSize: "0.8rem", marginTop: "2px" }}>
                        {dupResult.explanation}
                      </div>
                      <button 
                        type="button" 
                        className="btn btn-primary" 
                        onClick={() => handleMergeTask(dupResult.duplicateTaskId)}
                        style={{ padding: "4px 8px", fontSize: "0.75rem", marginTop: "8px" }}
                      >
                        Merge into task #{dupResult.duplicateTaskId} instead
                      </button>
                    </div>
                  </div>
                )}

                <div className="form-group">
                  <label className="form-label">Task Title</label>
                  <input 
                    type="text" 
                    className="form-input" 
                    placeholder="e.g. Implement JWT Authentication" 
                    value={newTitle}
                    onChange={(e) => setNewTitle(e.target.value)}
                    required
                  />
                </div>
                <div className="form-group">
                  <label className="form-label">Description</label>
                  <textarea 
                    className="form-input" 
                    rows="3" 
                    placeholder="Details about task objectives, database updates or API endpoints..." 
                    value={newDesc}
                    onChange={(e) => setNewDesc(e.target.value)}
                  />
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Priority</label>
                    <select className="form-select" value={newPriority} onChange={(e) => setNewPriority(e.target.value)}>
                      <option value="Low">Low</option>
                      <option value="Medium">Medium</option>
                      <option value="High">High</option>
                      <option value="Urgent">Urgent</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Assignee</label>
                    <select className="form-select" value={newAssignee} onChange={(e) => setNewAssignee(e.target.value)}>
                      {users.map(u => (
                        <option key={u.id} value={u.id}>{u.name} ({u.role})</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="form-row">
                  <div className="form-group">
                    <label className="form-label">Estimated Hours</label>
                    <input 
                      type="number" 
                      className="form-input" 
                      value={newEstHours}
                      onChange={(e) => setNewEstHours(e.target.value)}
                      min="1"
                    />
                  </div>
                  <div className="form-group">
                    <label className="form-label">Labels (comma-separated)</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      value={newLabels}
                      onChange={(e) => setNewLabels(e.target.value)}
                      placeholder="Backend, Bug, Docs"
                    />
                  </div>
                </div>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={() => setIsAddOpen(false)}>Cancel</button>
                <button type="submit" className="btn btn-primary">Create Task</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Task Details Modal */}
      {selectedTask && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: "800px" }}>
            <div className="modal-header">
              <div>
                <span className="task-priority-badge priority-low" style={{ marginRight: "8px" }}>
                  Task #{selectedTask.id}
                </span>
                <span className={`task-priority-badge priority-${selectedTask.priority.toLowerCase()}`}>
                  {selectedTask.priority}
                </span>
              </div>
              <button className="btn btn-secondary" onClick={() => setSelectedTask(null)} style={{ padding: "4px" }}>
                <X size={16} />
              </button>
            </div>
            
            <div className="modal-body">
              <h2 className="topbar-title" style={{ fontSize: "1.4rem", marginBottom: "16px" }}>{selectedTask.title}</h2>
              
              <div className="task-detail-grid">
                {/* Left Column: Description, Subtasks, Comments */}
                <div>
                  <div className="form-group">
                    <label className="form-label">Description</label>
                    <div style={{ fontSize: "0.9rem", color: "var(--text-secondary)", whiteSpace: "pre-line", backgroundColor: "var(--bg-tertiary)", padding: "12px", borderRadius: "var(--radius-md)", border: "1px solid var(--border-color)" }}>
                      {selectedTask.description || "No description provided."}
                    </div>
                  </div>

                  {/* AI Assistance Panel */}
                  <div className="ai-section">
                    <div className="ai-header">
                      <Sparkles size={16} />
                      <span>AI Planning Co-Pilot</span>
                      {aiLoading && <span style={{ fontSize: "0.75rem", fontStyle: "italic", marginLeft: "auto" }}>Estimating...</span>}
                    </div>
                    
                    {!aiResult && !aiLoading && (
                      <button type="button" className="btn btn-primary" onClick={() => handleRequestAiEstimation(selectedTask)} style={{ width: "100%", fontSize: "0.85rem" }}>
                        Ask AI for Subtasks & Hours Estimation
                      </button>
                    )}

                    {aiResult && (
                      <div className="ai-recommendation">
                        <div>
                          💡 AI estimation: <strong style={{ color: "var(--accent-gold)" }}>{aiResult.estimatedDays || 2.5} days</strong> ({Math.round(aiResult.estimatedDays * 8 || 20)} hours).
                        </div>
                        <div style={{ marginTop: "8px" }}>
                          <strong>Possible Blockers:</strong>
                          <ul style={{ paddingLeft: "16px", marginTop: "4px" }}>
                            {aiResult.blockers?.map((b, i) => <li key={i}>{b}</li>)}
                          </ul>
                        </div>
                        <div style={{ marginTop: "8px" }}>
                          <strong>Recommended Subtasks:</strong>
                          <ul className="ai-subtask-list">
                            {aiResult.subtasks?.map((s, i) => (
                              <li key={i} className="ai-subtask-item">
                                <span className="ai-badge">Checklist</span>
                                {s}
                              </li>
                            ))}
                          </ul>
                        </div>
                        
                        <div style={{ display: "flex", gap: "10px", marginTop: "12px" }}>
                          <button type="button" className="btn btn-primary" onClick={() => applyAiRecommendations(selectedTask)} style={{ flex: 1, fontSize: "0.8rem" }}>
                            Apply Recommendations
                          </button>
                          <button type="button" className="btn btn-secondary" onClick={() => setAiResult(null)} style={{ fontSize: "0.8rem" }}>
                            Dismiss
                          </button>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Subtasks Section */}
                  <div style={{ marginTop: "24px" }}>
                    <label className="form-label" style={{ display: "block", marginBottom: "8px" }}>Subtasks Checklist</label>
                    <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                      {selectedTask.subtasks?.map(sub => (
                        <label key={sub.id} className="ai-subtask-item" style={{ cursor: "pointer" }}>
                          <input 
                            type="checkbox" 
                            checked={sub.isCompleted} 
                            onChange={() => handleToggleSubtask(sub.id)}
                            style={{ accentColor: "var(--accent-gold)" }}
                          />
                          <span style={{ textDecoration: sub.isCompleted ? "line-through" : "none", color: sub.isCompleted ? "var(--text-muted)" : "var(--text-primary)" }}>
                            {sub.title}
                          </span>
                        </label>
                      ))}
                    </div>
                    <div style={{ display: "flex", gap: "8px", marginTop: "12px" }}>
                      <input 
                        type="text" 
                        className="form-input" 
                        placeholder="Add new subtask..." 
                        value={newSubtask} 
                        onChange={(e) => setNewSubtask(e.target.value)} 
                        style={{ flex: 1, padding: "6px 10px", fontSize: "0.85rem" }}
                      />
                      <button className="btn btn-secondary" onClick={handleAddSubtask} style={{ padding: "6px 12px", fontSize: "0.85rem" }}>
                        Add
                      </button>
                    </div>
                  </div>

                  {/* Comments Section */}
                  <div style={{ marginTop: "24px" }}>
                    <label className="form-label" style={{ display: "block", marginBottom: "8px" }}>Comments / Activity History</label>
                    <div style={{ display: "flex", flexDirection: "column", gap: "10px", maxHeight: "150px", overflowY: "auto", border: "1px solid var(--border-color)", padding: "12px", borderRadius: "var(--radius-md)" }}>
                      {(selectedTask.comments || []).length === 0 ? (
                        <div style={{ fontSize: "0.8rem", color: "var(--text-muted)", textAlign: "center" }}>No comments yet.</div>
                      ) : (
                        selectedTask.comments.map(c => (
                          <div key={c.id} style={{ fontSize: "0.85rem" }}>
                            <div style={{ display: "flex", justifyContent: "space-between", color: "var(--text-secondary)", fontSize: "0.75rem", marginBottom: "2px" }}>
                              <strong>{c.author}</strong>
                              <span>{c.created_at}</span>
                            </div>
                            <div style={{ color: "var(--text-primary)" }}>{c.content}</div>
                          </div>
                        ))
                      )}
                    </div>
                    <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
                      <input 
                        type="text" 
                        className="form-input" 
                        placeholder="Ask questions or post updates..." 
                        value={newComment} 
                        onChange={(e) => setNewComment(e.target.value)} 
                        style={{ flex: 1, padding: "6px 10px", fontSize: "0.85rem" }}
                      />
                      <button className="btn btn-primary" onClick={handleAddComment} style={{ padding: "6px 12px", fontSize: "0.85rem" }}>
                        Post
                      </button>
                    </div>
                  </div>
                </div>

                {/* Right Column: Meta details */}
                <div style={{ borderLeft: "1px solid var(--border-color)", paddingLeft: "24px" }}>
                  <div className="form-group">
                    <label className="form-label">Status</label>
                    <select 
                      className="form-select" 
                      value={selectedTask.status} 
                      onChange={(e) => {
                        updateTask(selectedTask.id, { status: e.target.value });
                        setSelectedTask({ ...selectedTask, status: e.target.value });
                      }}
                    >
                      <option value="Todo">Todo</option>
                      <option value="Doing">Doing</option>
                      <option value="Done">Done</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Assignee</label>
                    <select 
                      className="form-select" 
                      value={selectedTask.assigneeId} 
                      onChange={(e) => {
                        updateTask(selectedTask.id, { assigneeId: e.target.value });
                        setSelectedTask({ ...selectedTask, assigneeId: e.target.value });
                      }}
                    >
                      {users.map(u => (
                        <option key={u.id} value={u.id}>{u.name}</option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">Estimated Hours</label>
                    <input 
                      type="number" 
                      className="form-input" 
                      value={selectedTask.estimatedHours} 
                      onChange={(e) => {
                        const hrs = Number(e.target.value);
                        updateTask(selectedTask.id, { estimatedHours: hrs });
                        setSelectedTask({ ...selectedTask, estimatedHours: hrs });
                      }}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Logged Hours</label>
                    <input 
                      type="number" 
                      className="form-input" 
                      value={selectedTask.actualHours || 0} 
                      onChange={(e) => {
                        const hrs = Number(e.target.value);
                        updateTask(selectedTask.id, { actualHours: hrs });
                        setSelectedTask({ ...selectedTask, actualHours: hrs });
                      }}
                    />
                  </div>

                  {currentRole === "Developer" ? (
                    <div className="rbac-restriction">
                      Only Admins/Managers can delete tasks.
                    </div>
                  ) : (
                    <button 
                      type="button" 
                      className="btn btn-danger" 
                      onClick={() => {
                        if (confirm("Are you sure you want to delete this task?")) {
                          deleteTask(selectedTask.id);
                          setSelectedTask(null);
                        }
                      }}
                      style={{ width: "100%", marginTop: "16px" }}
                    >
                      Delete Task
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
