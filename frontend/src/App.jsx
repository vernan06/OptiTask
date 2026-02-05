import React, { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import Assistant from "./Assistant";
import {
  Inbox,
  Calendar,
  CheckCircle,
  Play,
  Pause,
  RotateCcw,
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  Check,
  Zap,
  Menu,
  X,
  Command,
} from "lucide-react";

const API = "http://127.0.0.1:8000";

function pad2(n) {
  return String(n).padStart(2, "0");
}

function minsToHHMM(m) {
  const hh = Math.floor(m / 60);
  const mm = m % 60;
  return `${pad2(hh)}:${pad2(mm)}`;
}

export default function App() {
  // Layout
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [timetableExpanded, setTimetableExpanded] = useState(false);
  const [activeTab, setActiveTab] = useState("inbox"); // inbox | upcoming | completed

  // Tasks
  const [tasks, setTasks] = useState([]);
  const [quickTitle, setQuickTitle] = useState("");

  // Calendar
  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0]
  );

  // Command Bar
  const [commandOpen, setCommandOpen] = useState(false);
  const [commandText, setCommandText] = useState("");
  const [commandError, setCommandError] = useState("");

  // Ghost scheduling
  const [ghosts, setGhosts] = useState([]);

  // Focus Timer (inline edit)
  const [sessionTotal, setSessionTotal] = useState(25 * 60);
  const [timeLeft, setTimeLeft] = useState(25 * 60);
  const [isActive, setIsActive] = useState(false);
  const [isEditing, setIsEditing] = useState(null); // 'm' | 's' | null
  const [editVal, setEditVal] = useState("");

  // Flow HUD
  const [flowMode, setFlowMode] = useState(false);
  const [currentFlowTask, setCurrentFlowTask] = useState(null);

  const notifiedDoneRef = useRef(false);

  const fetchTasks = async () => {
    const res = await axios.get(`${API}/tasks`);
    setTasks(res.data || []);
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  // Timer tick
  useEffect(() => {
    let interval = null;
    if (isActive && timeLeft > 0) {
      interval = setInterval(() => setTimeLeft((t) => t - 1), 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isActive, timeLeft]);

  // Notifications (when timer finishes)
  useEffect(() => {
    if (timeLeft === 0 && !notifiedDoneRef.current) {
      notifiedDoneRef.current = true;
      setIsActive(false);

      if ("Notification" in window) {
        if (Notification.permission === "granted") {
          new Notification("Session complete", {
            body: "Reset or start the next block.",
          });
        }
      }
    }
    if (timeLeft > 0) {
      notifiedDoneRef.current = false;
    }
  }, [timeLeft]);

  // Ask notification permission once
  useEffect(() => {
    if ("Notification" in window && Notification.permission === "default") {
      Notification.requestPermission().catch(() => {});
    }
  }, []);

  const handleTimerEdit = (type) => {
    setIsEditing(type);
    setEditVal("");
    setIsActive(false);
  };

  const saveTimer = () => {
    const v = Math.max(0, Math.min(99, parseInt(editVal || "0", 10) || 0));
    const curM = Math.floor(timeLeft / 60);
    const curS = timeLeft % 60;

    let newM = curM;
    let newS = curS;

    if (isEditing === "m") newM = v;
    if (isEditing === "s") newS = Math.max(0, Math.min(59, v));

    const newTotal = newM * 60 + newS;

    setSessionTotal(newTotal);
    setTimeLeft(newTotal);
    setIsEditing(null);
  };

  const resetTimer = () => {
    setIsActive(false);
    setFlowMode(false);
    setCurrentFlowTask(null);
    setSessionTotal(25 * 60);
    setTimeLeft(25 * 60);
  };

  const startStopTimer = () => {
    // If starting: enter flow mode and choose a task (top of active list)
    if (!isActive) {
      const pick = filteredActive[0] || null;
      setCurrentFlowTask(pick);
      setFlowMode(true);
    }
    setIsActive((v) => !v);
  };

  const addTask = async () => {
    if (!quickTitle.trim()) return;
    await axios.post(`${API}/tasks`, {
      name: quickTitle.trim(),
      category: "general",
      priority: 3,
      deadline: selectedDate,
      start_time: "",
      duration: 30,
      status: 0,
    });
    setQuickTitle("");
    await fetchTasks();
  };

  const completeTask = async (id) => {
    await axios.patch(`${API}/tasks/${id}`, { status: 1 });
    await fetchTasks();
  };

  const deleteTask = async (id) => {
    await axios.delete(`${API}/tasks/${id}`);
    await fetchTasks();
  };

  const executeCommand = async () => {
    if (!commandText.trim()) return;
    try {
      setCommandError("");
      await axios.post(`${API}/command`, { text: commandText.trim() });
      setCommandText("");
      setCommandOpen(false);
      await fetchTasks();
    } catch (err) {
      setCommandError(err?.response?.data?.detail || "Could not parse that");
    }
  };

  // Keyboard shortcut: Ctrl/Cmd+K
  useEffect(() => {
    const handler = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setCommandOpen(true);
        setCommandError("");
      }
      if (e.key === "Escape") {
        setCommandOpen(false);
        setCommandError("");
        setFlowMode(false);
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, []);

  // Filter logic
  const todayIso = useMemo(() => new Date().toISOString().split("T")[0], []);

  const filtered = useMemo(() => {
    if (activeTab === "inbox") return tasks.filter((t) => t.status === 0);
    if (activeTab === "completed") return tasks.filter((t) => t.status === 1);
    // upcoming
    return tasks.filter((t) => t.status === 0 && (t.deadline || "") >= todayIso);
  }, [tasks, activeTab, todayIso]);

  const filteredActive = useMemo(() => tasks.filter((t) => t.status === 0), [tasks]);

  const scheduledForSelectedDate = useMemo(() => {
    return tasks.filter(
      (t) => (t.deadline || "") === selectedDate && (t.start_time || "").trim() !== ""
    );
  }, [tasks, selectedDate]);

  // Fetch ghost schedule when timetable expands OR date changes OR tasks change
  useEffect(() => {
    if (!timetableExpanded) return;
    axios
      .get(`${API}/ghost-schedule`, { params: { date: selectedDate } })
      .then((res) => setGhosts(res.data?.suggestions || []))
      .catch(() => setGhosts([]));
  }, [timetableExpanded, selectedDate, tasks]);

  // Timetable slots: 08:00–20:00 in 30-min steps
  const slots = useMemo(() => {
    const out = [];
    const start = 8 * 60;
    const end = 20 * 60;
    for (let m = start; m <= end; m += 30) out.push(m);
    return out;
  }, []);

  const findBlockAt = (hhmm) => {
    return scheduledForSelectedDate.find((t) => (t.start_time || "") === hhmm) || null;
  };

  const findGhostAt = (hhmm) => {
    return ghosts.find((g) => g.suggested_time === hhmm) || null;
  };

  const solidifyGhost = async (g) => {
    await axios.post(`${API}/solidify-ghost/${g.task_id}`, {
      time_slot: g.suggested_time,
      deadline: selectedDate,
    });
    await fetchTasks();
  };

  // Flow progress
  const progressPct = sessionTotal > 0 ? ((sessionTotal - timeLeft) / sessionTotal) * 100 : 0;

  return (
    <div className="app-container">
      {/* Command Bar */}
      {commandOpen && (
        <div className="overlay" onClick={() => setCommandOpen(false)}>
          <div className="command-modal" onClick={(e) => e.stopPropagation()}>
            <div className="command-row">
              <Command size={18} className="command-icon" />
              <input
                autoFocus
                className="command-input"
                placeholder='Try: "Gym friday 6pm 90m P1"'
                value={commandText}
                onChange={(e) => setCommandText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") executeCommand();
                }}
              />
            </div>

            {commandError && <div className="command-error">{commandError}</div>}

            <div className="command-foot">
              Enter creates instantly • Esc closes • Ctrl/Cmd+K opens
            </div>
          </div>
        </div>
      )}

      {/* Flow HUD */}
      {flowMode && (
        <div className="flow">
          <button className="flow-exit" onClick={() => setFlowMode(false)}>
            <X size={18} />
          </button>

          <div className="flow-label">FOCUS BLOCK</div>
          <div className="flow-title">{currentFlowTask?.name || "Deep work"}</div>

          <div className="flow-time">
            {pad2(Math.floor(timeLeft / 60))}
            <span className="flow-colon">:</span>
            {pad2(timeLeft % 60)}
          </div>

          <div className="flow-bar">
            <div className="flow-bar-fill" style={{ width: `${Math.min(100, Math.max(0, progressPct))}%` }} />
          </div>

          <div className="flow-controls">
            <button className="btn-primary" onClick={startStopTimer}>
              {isActive ? <Pause size={18} /> : <Play size={18} />}
            </button>
            <button className="btn-ghost" onClick={resetTimer}>
              <RotateCcw size={18} />
            </button>
          </div>

          {filteredActive.length > 1 && (
            <div className="flow-next">
              <div className="flow-next-label">NEXT</div>
              <div className="flow-next-title">{filteredActive[1]?.name}</div>
            </div>
          )}
        </div>
      )}

      {/* Sidebar */}
      <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
        <div className="brand">
          <span>⚡</span>OptiTask<span>⚡</span>
        </div>

        <nav>
          <div
            className={`nav-item ${activeTab === "inbox" ? "active" : ""}`}
            onClick={() => setActiveTab("inbox")}
          >
            <Inbox size={18} /> Inbox
          </div>
          <div
            className={`nav-item ${activeTab === "upcoming" ? "active" : ""}`}
            onClick={() => setActiveTab("upcoming")}
          >
            <Calendar size={18} /> Upcoming
          </div>
          <div
            className={`nav-item ${activeTab === "completed" ? "active" : ""}`}
            onClick={() => setActiveTab("completed")}
          >
            <CheckCircle size={18} /> Done
          </div>
        </nav>

        <div className="timer-box">
          <div className="timer-display">
            {isEditing === "m" ? (
              <input
                autoFocus
                className="timer-input"
                value={editVal}
                onChange={(e) => setEditVal(e.target.value)}
                onBlur={saveTimer}
                onKeyDown={(e) => e.key === "Enter" && saveTimer()}
              />
            ) : (
              <span className="timer-digit" onClick={() => handleTimerEdit("m")}>
                {pad2(Math.floor(timeLeft / 60))}
              </span>
            )}
            :
            {isEditing === "s" ? (
              <input
                autoFocus
                className="timer-input"
                value={editVal}
                onChange={(e) => setEditVal(e.target.value)}
                onBlur={saveTimer}
                onKeyDown={(e) => e.key === "Enter" && saveTimer()}
              />
            ) : (
              <span className="timer-digit" onClick={() => handleTimerEdit("s")}>
                {pad2(timeLeft % 60)}
              </span>
            )}
          </div>

          <div className="timer-actions">
            <button className="btn-primary" onClick={startStopTimer}>
              {isActive ? <Pause size={18} /> : <Play size={18} />}
            </button>
            <button className="btn-ghost" onClick={resetTimer}>
              <RotateCcw size={18} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main">
        <header className="top-nav">
          <button className="toggle-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>

          <button className="toggle-btn" onClick={() => setCommandOpen(true)}>
            <Command size={16} />
            <span className="kbd">Ctrl K</span>
          </button>

          <div className="date-chip">
            {new Date().toLocaleDateString(undefined, {
              weekday: "long",
              month: "short",
              day: "numeric",
            })}
          </div>
        </header>

        <div className="content-grid">
          {/* Tasks area */}
          <div className="task-area">
            <h2 className="page-title">
              {activeTab === "inbox" ? "Capture" : activeTab === "upcoming" ? "Horizon" : "Archive"}
            </h2>

            <div className="input-group">
              <input
                className="input-clean"
                placeholder="Drop a task. Hit Enter."
                value={quickTitle}
                onChange={(e) => setQuickTitle(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addTask()}
              />
              <button className="btn-primary" onClick={addTask}>
                <Plus size={18} />
              </button>
            </div>

            {filtered.map((t) => (
              <div className="task-card" key={t.id}>
                <div>
                  <div className="task-title">{t.name}</div>
                  <div className="task-sub">
                    {t.category} • P{t.priority} • {t.deadline || "No date"} {t.start_time ? `• ${t.start_time}` : ""}
                  </div>
                </div>

                <div className="task-actions">
                  {t.status === 0 && (
                    <button className="toggle-btn" onClick={() => completeTask(t.id)} title="Mark done">
                      <Check size={16} />
                    </button>
                  )}
                  <button className="toggle-btn" onClick={() => deleteTask(t.id)} title="Delete">
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Right panels */}
          <div className="right-panels">
            {/* Calendar pane hides when timetable expanded */}
            <div className={`calendar-pane ${timetableExpanded ? "hidden" : ""}`}>
              <div className="pane-title">Schedule</div>

              <div className="cal-grid">
                {Array.from({ length: 31 }, (_, i) => {
                  const day = i + 1;
                  const iso = `${selectedDate.slice(0, 8)}${pad2(day)}`;
                  const active = iso === selectedDate;
                  return (
                    <div
                      key={day}
                      className={`cal-day ${active ? "active" : ""}`}
                      onClick={() => setSelectedDate(iso)}
                      title={iso}
                    >
                      {day}
                    </div>
                  );
                })}
              </div>

              <div className="mini-note">
                Pick a date • Expand timeline for ghost scheduling
              </div>
            </div>

            {/* Timetable pane */}
            <div className={`timetable-pane ${timetableExpanded ? "expanded" : "collapsed"}`}>
              <button
                className="timetable-toggle"
                onClick={() => setTimetableExpanded(!timetableExpanded)}
                title={timetableExpanded ? "Collapse timeline" : "Expand timeline"}
              >
                {timetableExpanded ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
              </button>

              <div className="timetable-content">
                <div className="timetable-head">
                  <div className="timetable-title">
                    Daily Flow <Zap size={16} className="zap" />
                  </div>
                  <div className="timetable-sub">{selectedDate}</div>
                </div>

                {slots.map((m) => {
                  const label = minsToHHMM(m);
                  const real = findBlockAt(label);
                  const ghost = !real ? findGhostAt(label) : null;

                  return (
                    <div className="hour-row" key={label}>
                      <div className="hour-label">{label}</div>

                      {real ? (
                        <div className="time-block">
                          {real.name}
                          <div className="time-sub">P{real.priority} • {real.duration}m</div>
                        </div>
                      ) : ghost ? (
                        <div
                          className="time-block ghost"
                          onClick={() => solidifyGhost(ghost)}
                          title="Click to lock it in"
                        >
                          <div className="ghost-top">Ghost slot</div>
                          {ghost.name}
                          <div className="time-sub">P{ghost.priority} • {ghost.duration}m • click to schedule</div>
                        </div>
                      ) : (
                        <div className="empty-line" />
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </main>
      <Assistant onTaskUpdate={fetchTasks} />
    </div>
  );
}