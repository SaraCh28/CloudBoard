/**
 * CloudBoard – Global Search Bar Component (Module 6)
 *
 * Features:
 *  - Debounced live search (300ms)
 *  - Dropdown results panel grouped by type
 *  - Keyboard navigation (Escape to close, ArrowUp/Down, Enter to select)
 *  - Requires auth token from localStorage
 *  - Type badges: task (blue), project (gold), org (green), member (gray)
 */

import React, { useState, useEffect, useRef, useCallback } from "react"
import { Search, X, Loader2, FileText, FolderKanban, Building2, User } from "lucide-react"

const API_BASE = "http://localhost:8000/api/v1"

const TYPE_CONFIG = {
  task:         { label: "Task",         color: "var(--accent-blue)",   Icon: FileText       },
  project:      { label: "Project",      color: "var(--accent-gold)",   Icon: FolderKanban   },
  organization: { label: "Org",          color: "var(--accent-green)",  Icon: Building2      },
  member:       { label: "Member",       color: "var(--text-secondary)", Icon: User          },
}

function TypeBadge({ type }) {
  const { label, color } = TYPE_CONFIG[type] || {}
  return (
    <span style={{
      fontSize: "0.65rem",
      padding: "1px 5px",
      borderRadius: "3px",
      fontWeight: 700,
      textTransform: "uppercase",
      backgroundColor: `${color}22`,
      color,
      border: `1px solid ${color}44`,
      flexShrink: 0,
    }}>
      {label}
    </span>
  )
}

export default function GlobalSearch({ onNavigate }) {
  const [query, setQuery]           = useState("")
  const [results, setResults]       = useState([])
  const [loading, setLoading]       = useState(false)
  const [open, setOpen]             = useState(false)
  const [activeIdx, setActiveIdx]   = useState(-1)
  const inputRef = useRef(null)
  const panelRef = useRef(null)
  const debounceRef = useRef(null)

  // ── Fetch ────────────────────────────────────────────────────────
  const doSearch = useCallback(async (q) => {
    if (!q.trim()) { setResults([]); setOpen(false); return }
    const token = localStorage.getItem("cb_access_token")
    if (!token) return

    setLoading(true)
    try {
      const res = await fetch(
        `${API_BASE}/search?q=${encodeURIComponent(q)}&limit=12`,
        { headers: { Authorization: `Bearer ${token}` } }
      )
      if (!res.ok) throw new Error("Search failed")
      const data = await res.json()
      setResults(data.results)
      setOpen(true)
      setActiveIdx(-1)
    } catch {
      setResults([])
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    clearTimeout(debounceRef.current)
    if (!query.trim()) { setResults([]); setOpen(false); return }
    debounceRef.current = setTimeout(() => doSearch(query), 300)
    return () => clearTimeout(debounceRef.current)
  }, [query, doSearch])

  // ── Keyboard nav ─────────────────────────────────────────────────
  const handleKeyDown = (e) => {
    if (!open) return
    if (e.key === "Escape") { setOpen(false); inputRef.current?.blur() }
    if (e.key === "ArrowDown") { e.preventDefault(); setActiveIdx(i => Math.min(i + 1, results.length - 1)) }
    if (e.key === "ArrowUp")   { e.preventDefault(); setActiveIdx(i => Math.max(i - 1, -1)) }
    if (e.key === "Enter" && activeIdx >= 0) selectHit(results[activeIdx])
  }

  const selectHit = (hit) => {
    setOpen(false)
    setQuery("")
    if (onNavigate) onNavigate(hit)
  }

  // ── Click outside ────────────────────────────────────────────────
  useEffect(() => {
    const handler = (e) => {
      if (!panelRef.current?.contains(e.target) && !inputRef.current?.contains(e.target)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handler)
    return () => document.removeEventListener("mousedown", handler)
  }, [])

  return (
    <div style={{ position: "relative", width: "320px" }}>
      {/* Input */}
      <div style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        background: "var(--bg-tertiary)",
        border: `1px solid ${open ? "var(--border-focus)" : "var(--border-color)"}`,
        borderRadius: "var(--radius-md)",
        padding: "7px 12px",
        transition: "border-color 0.15s ease",
      }}>
        {loading
          ? <Loader2 size={15} style={{ color: "var(--text-muted)", animation: "spin 1s linear infinite", flexShrink: 0 }} />
          : <Search size={15} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
        }
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => query && setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search tasks, projects, members…"
          id="global-search-input"
          aria-label="Global search"
          style={{
            background: "none",
            border: "none",
            outline: "none",
            fontSize: "0.875rem",
            color: "var(--text-primary)",
            flex: 1,
            minWidth: 0,
          }}
        />
        {query && (
          <button
            onClick={() => { setQuery(""); setResults([]); setOpen(false) }}
            style={{ background: "none", border: "none", cursor: "pointer", padding: 0, display: "flex", color: "var(--text-muted)" }}
            aria-label="Clear search"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Dropdown */}
      {open && (
        <div
          ref={panelRef}
          role="listbox"
          style={{
            position: "absolute",
            top: "calc(100% + 6px)",
            left: 0,
            right: 0,
            background: "var(--bg-secondary)",
            border: "1px solid var(--border-color)",
            borderRadius: "var(--radius-lg)",
            boxShadow: "0 8px 32px rgba(0,0,0,0.5)",
            zIndex: 9999,
            maxHeight: "380px",
            overflowY: "auto",
          }}
        >
          {results.length === 0 ? (
            <div style={{ padding: "20px", textAlign: "center", color: "var(--text-muted)", fontSize: "0.875rem" }}>
              No results for <strong style={{ color: "var(--text-secondary)" }}>"{query}"</strong>
            </div>
          ) : (
            <>
              <div style={{ padding: "8px 12px 4px", fontSize: "0.7rem", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", color: "var(--text-muted)", borderBottom: "1px solid var(--border-color)" }}>
                {results.length} result{results.length !== 1 ? "s" : ""}
              </div>
              {results.map((hit, idx) => {
                const { Icon } = TYPE_CONFIG[hit.type] || { Icon: Search }
                const isActive = idx === activeIdx
                return (
                  <div
                    key={`${hit.type}-${hit.id}`}
                    role="option"
                    aria-selected={isActive}
                    onClick={() => selectHit(hit)}
                    onMouseEnter={() => setActiveIdx(idx)}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: "10px",
                      padding: "10px 14px",
                      cursor: "pointer",
                      background: isActive ? "var(--bg-tertiary)" : "transparent",
                      borderBottom: "1px solid var(--border-color)",
                      transition: "background 0.1s ease",
                    }}
                  >
                    <Icon size={15} style={{ color: "var(--text-muted)", flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: "0.9rem", fontWeight: 600, color: "var(--text-primary)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                        {hit.title}
                      </div>
                      {hit.subtitle && (
                        <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginTop: "1px" }}>
                          {hit.subtitle}
                        </div>
                      )}
                    </div>
                    <TypeBadge type={hit.type} />
                  </div>
                )
              })}
            </>
          )}
        </div>
      )}

      {/* Spin keyframe (injected once) */}
      <style>{`@keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }`}</style>
    </div>
  )
}
