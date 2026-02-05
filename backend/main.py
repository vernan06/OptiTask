import os
import sqlite3
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import ctypes
from nl_parser import parse_command, validate_date_time
from ai_assistant import process_message as ai_process_message


# -----------------------------
# Paths
# -----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tasks.db")

C_CORE_DIR = os.path.join(BASE_DIR, "c_core")
DLL_PATH = os.path.join(C_CORE_DIR, "task_manager.dll")


# -----------------------------
# C Core (ctypes)
# -----------------------------
def load_c_core():
    if not os.path.exists(DLL_PATH):
        raise RuntimeError(
            f"task_manager.dll not found at: {DLL_PATH}\n"
            f"Build it first: backend\\c_core\\build.bat"
        )

    lib = ctypes.CDLL(DLL_PATH)

    # void tm_init(void);
    lib.tm_init.argtypes = []
    lib.tm_init.restype = None

    # void tm_reset(void);
    lib.tm_reset.argtypes = []
    lib.tm_reset.restype = None

    # int tm_add_task(const char*, const char*, int, const char*, const char*, int, int);
    lib.tm_add_task.argtypes = [
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int
    ]
    lib.tm_add_task.restype = ctypes.c_int

    # int tm_add_task_with_id(int, const char*, const char*, int, const char*, const char*, int, int);
    lib.tm_add_task_with_id.argtypes = [
        ctypes.c_int,
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int
    ]
    lib.tm_add_task_with_id.restype = ctypes.c_int

    # int tm_update_task(int, int, const char*, const char*, int, int);
    # priority=-1 keep, deadline NULL keep, start_time NULL keep, duration=-1 keep, status=-1 keep
    lib.tm_update_task.argtypes = [
        ctypes.c_int, ctypes.c_int,
        ctypes.c_char_p, ctypes.c_char_p,
        ctypes.c_int, ctypes.c_int
    ]
    lib.tm_update_task.restype = ctypes.c_int

    # int tm_delete_task(int);
    lib.tm_delete_task.argtypes = [ctypes.c_int]
    lib.tm_delete_task.restype = ctypes.c_int

    return lib


lib = load_c_core()
lib.tm_init()


# -----------------------------
# SQLite
# -----------------------------
def db_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def db_init():
    conn = db_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
          id INTEGER PRIMARY KEY,
          name TEXT NOT NULL,
          category TEXT NOT NULL DEFAULT 'general',
          priority INTEGER NOT NULL DEFAULT 3,
          deadline TEXT NOT NULL DEFAULT '',
          start_time TEXT NOT NULL DEFAULT '',
          duration INTEGER NOT NULL DEFAULT 30,
          status INTEGER NOT NULL DEFAULT 0
        );
        """
    )
    conn.commit()
    conn.close()


def sync_db_to_c():
    """
    Load DB rows into the C core with the SAME ids.
    """
    lib.tm_reset()

    conn = db_conn()
    rows = conn.execute(
        "SELECT id, name, category, priority, deadline, start_time, duration, status FROM tasks"
    ).fetchall()
    conn.close()

    for r in rows:
        lib.tm_add_task_with_id(
            int(r["id"]),
            str(r["name"]).encode("utf-8"),
            str(r["category"]).encode("utf-8"),
            int(r["priority"]),
            str(r["deadline"]).encode("utf-8"),
            str(r["start_time"]).encode("utf-8"),
            int(r["duration"]),
            int(r["status"]),
        )


db_init()
sync_db_to_c()


# -----------------------------
# FastAPI
# -----------------------------
app = FastAPI(title="Smart Task Prioritizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Models
# -----------------------------
class TaskCreate(BaseModel):
    name: str
    category: str = "general"
    priority: int = 3
    deadline: str = ""          # YYYY-MM-DD
    start_time: str = ""        # HH:MM
    duration: int = 30          # minutes
    status: int = 0             # 0=active, 1=done


class TaskPatch(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[int] = None
    deadline: Optional[str] = None
    start_time: Optional[str] = None
    duration: Optional[int] = None
    status: Optional[int] = None


class CommandIn(BaseModel):
    text: str


class ChatIn(BaseModel):
    message: str


# -----------------------------
# Helpers
# -----------------------------
def _today_iso() -> str:
    return datetime.now().date().isoformat()


def _norm_date(d: str) -> str:
    return (d or "").strip()


def _norm_time(t: str) -> str:
    return (t or "").strip()


# -----------------------------
# Core endpoints
# -----------------------------
@app.get("/tasks")
def list_tasks():
    conn = db_conn()
    rows = conn.execute(
        "SELECT id, name, category, priority, deadline, start_time, duration, status "
        "FROM tasks ORDER BY status ASC, priority ASC, deadline ASC, start_time ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/tasks")
def create_task(t: TaskCreate):
    name = (t.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="name is required")

    deadline = _norm_date(t.deadline) or _today_iso()
    start_time = _norm_time(t.start_time)

    # Validate date/time is not in the past
    validation = validate_date_time(deadline, start_time)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    # Use C-core as ID authority
    new_id = lib.tm_add_task(
        name.encode("utf-8"),
        (t.category or "general").encode("utf-8"),
        int(t.priority),
        deadline.encode("utf-8"),
        start_time.encode("utf-8"),
        int(t.duration),
        int(t.status),
    )

    conn = db_conn()
    conn.execute(
        "INSERT INTO tasks(id, name, category, priority, deadline, start_time, duration, status) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (int(new_id), name, t.category or "general", int(t.priority), deadline, start_time, int(t.duration), int(t.status)),
    )
    conn.commit()
    conn.close()

    return {"id": int(new_id)}


@app.patch("/tasks/{task_id}")
def patch_task(task_id: int, p: TaskPatch):
    conn = db_conn()
    row = conn.execute(
        "SELECT id, name, category, priority, deadline, start_time, duration, status FROM tasks WHERE id=?",
        (task_id,),
    ).fetchone()

    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="task not found")

    new_name = (p.name if p.name is not None else row["name"])
    new_category = (p.category if p.category is not None else row["category"])
    new_priority = (p.priority if p.priority is not None else row["priority"])
    new_deadline = (_norm_date(p.deadline) if p.deadline is not None else row["deadline"])
    new_start_time = (_norm_time(p.start_time) if p.start_time is not None else row["start_time"])
    new_duration = (p.duration if p.duration is not None else row["duration"])
    new_status = (p.status if p.status is not None else row["status"])

    if not str(new_name).strip():
        conn.close()
        raise HTTPException(status_code=400, detail="name cannot be empty")

    conn.execute(
        "UPDATE tasks SET name=?, category=?, priority=?, deadline=?, start_time=?, duration=?, status=? WHERE id=?",
        (
            str(new_name).strip(),
            str(new_category).strip() or "general",
            int(new_priority),
            str(new_deadline).strip(),
            str(new_start_time).strip(),
            int(new_duration),
            int(new_status),
            int(task_id),
        ),
    )
    conn.commit()
    conn.close()

    # Sync to C
    lib.tm_update_task(
        int(task_id),
        int(new_priority),
        str(new_deadline).encode("utf-8"),
        str(new_start_time).encode("utf-8"),
        int(new_duration),
        int(new_status),
    )

    return {"ok": True}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = db_conn()
    cur = conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="task not found")

    lib.tm_delete_task(int(task_id))
    return {"ok": True}


# -----------------------------
# Phase 1: Command Bar endpoint
# -----------------------------
@app.post("/command")
def command(cmd: CommandIn):
    parsed = parse_command(cmd.text)

    # Check for parse error (including past date validation done in parser)
    if not parsed["valid"]:
        error_msg = parsed.get("error") or "Could not parse that command"
        raise HTTPException(status_code=400, detail=error_msg)

    deadline = parsed["deadline"] or _today_iso()
    start_time = parsed["start_time"] or ""

    # Validate date/time is not in the past
    validation = validate_date_time(deadline, start_time)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])

    new_id = lib.tm_add_task(
        parsed["name"].encode("utf-8"),
        parsed["category"].encode("utf-8"),
        int(parsed["priority"]),
        deadline.encode("utf-8"),
        start_time.encode("utf-8"),
        int(parsed["duration"]),
        int(parsed["status"]),
    )

    conn = db_conn()
    conn.execute(
        "INSERT INTO tasks(id, name, category, priority, deadline, start_time, duration, status) "
        "VALUES(?,?,?,?,?,?,?,?)",
        (
            int(new_id),
            parsed["name"],
            parsed["category"],
            int(parsed["priority"]),
            deadline,
            start_time,
            int(parsed["duration"]),
            int(parsed["status"]),
        ),
    )
    conn.commit()
    conn.close()

    return {"id": int(new_id), "parsed": parsed}


# -----------------------------
# AI Assistant Chat
# -----------------------------
@app.post("/chat")
def chat(chat_in: ChatIn):
    """
    AI Assistant endpoint. Processes natural language and returns response + action.
    """
    # Get current tasks for context
    conn = db_conn()
    rows = conn.execute(
        "SELECT id, name, priority, deadline, status FROM tasks WHERE status=0 ORDER BY priority ASC LIMIT 10"
    ).fetchall()
    conn.close()
    
    tasks = [dict(r) for r in rows]
    
    # Process with AI assistant
    result = ai_process_message(chat_in.message, tasks)
    
    action = result.get("action", "reply")
    response = result.get("response", "I understand.")
    
    # Handle actions that modify tasks
    if action == "add_task" and result.get("task_text"):
        from nl_parser import parse_command
        parsed = parse_command(result["task_text"])
        if parsed["valid"]:
            deadline = parsed["deadline"] or _today_iso()
            start_time = parsed["start_time"] or ""
            
            new_id = lib.tm_add_task(
                parsed["name"].encode("utf-8"),
                parsed["category"].encode("utf-8"),
                int(parsed["priority"]),
                deadline.encode("utf-8"),
                start_time.encode("utf-8"),
                int(parsed["duration"]),
                0,
            )
            
            conn = db_conn()
            conn.execute(
                "INSERT INTO tasks (id, name, category, priority, deadline, start_time, duration, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id, parsed["name"], parsed["category"], parsed["priority"], deadline, start_time, parsed["duration"], 0)
            )
            conn.commit()
            conn.close()
            
            response = f"Done! Added '{parsed['name']}' for {deadline}."
            result["created_task"] = {"id": new_id, "name": parsed["name"]}
    
    elif action == "complete_task" and result.get("task_id"):
        task_id = result["task_id"]
        lib.tm_update_task(task_id, -1, None, None, -1, 1)
        conn = db_conn()
        conn.execute("UPDATE tasks SET status=1 WHERE id=?", (task_id,))
        conn.commit()
        conn.close()
    
    elif action == "delete_task" and result.get("task_id"):
        task_id = result["task_id"]
        lib.tm_delete_task(task_id)
        conn = db_conn()
        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        conn.commit()
        conn.close()
    
    elif action == "list_tasks":
        if tasks:
            task_list = "\n".join([f"#{t['id']}: {t['name']} (P{t['priority']})" for t in tasks])
            response = f"Here's your schedule:\n{task_list}"
        else:
            response = "Your schedule is clear! No active tasks."
    
    return {"action": action, "response": response, "data": result}


# -----------------------------
# Phase 2: Ghost scheduling
# -----------------------------
@app.get("/ghost-schedule")
def ghost_schedule(date: Optional[str] = None):
    """
    Suggest slots for unscheduled tasks for a given date (YYYY-MM-DD).
    Uses 30-min grid between 08:00 and 20:00.
    """
    target_date = (date or _today_iso()).strip()

    conn = db_conn()

    unscheduled = conn.execute(
        """
        SELECT id, name, priority, duration, deadline
        FROM tasks
        WHERE status=0
          AND (start_time='' OR start_time IS NULL)
        ORDER BY priority ASC, deadline ASC
        LIMIT 6
        """
    ).fetchall()

    scheduled = conn.execute(
        """
        SELECT start_time, duration
        FROM tasks
        WHERE status=0
          AND deadline=?
          AND start_time!=''
        """,
        (target_date,),
    ).fetchall()

    conn.close()

    occupied = []
    for r in scheduled:
        st = str(r["start_time"] or "").strip()
        if not st:
            continue
        try:
            hh, mm = map(int, st.split(":"))
        except Exception:
            continue
        start_m = hh * 60 + mm
        dur = int(r["duration"] or 0)
        occupied.append((start_m, start_m + max(dur, 0)))

    def overlaps(a0, a1):
        for b0, b1 in occupied:
            if not (a1 <= b0 or a0 >= b1):
                return True
        return False

    work_start = 8 * 60
    work_end = 20 * 60
    step = 30

    suggestions = []

    for r in unscheduled:
        task_id = int(r["id"])
        name = str(r["name"])
        priority = int(r["priority"])
        duration = max(int(r["duration"] or 30), 15)

        slot = None
        cur = work_start
        while cur + duration <= work_end:
            if not overlaps(cur, cur + duration):
                slot = cur
                break
            cur += step

        if slot is None:
            slot = work_start  # fallback

        hh = slot // 60
        mm = slot % 60
        suggestions.append(
            {
                "task_id": task_id,
                "name": name,
                "priority": priority,
                "duration": duration,
                "suggested_time": f"{hh:02d}:{mm:02d}",
                "deadline": target_date,
            }
        )
        occupied.append((slot, slot + duration))

    return {"date": target_date, "suggestions": suggestions}


@app.post("/solidify-ghost/{task_id}")
def solidify_ghost(task_id: int, payload: dict):
    time_slot = (payload.get("time_slot") or "").strip()
    deadline = (payload.get("deadline") or "").strip()

    if not time_slot:
        raise HTTPException(status_code=400, detail="time_slot is required")

    conn = db_conn()
    row = conn.execute("SELECT id FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="task not found")

    if deadline:
        conn.execute("UPDATE tasks SET start_time=?, deadline=? WHERE id=?", (time_slot, deadline, task_id))
    else:
        conn.execute("UPDATE tasks SET start_time=? WHERE id=?", (time_slot, task_id))

    conn.commit()
    conn.close()

    # Sync to C (keep other values by passing -1 and NULL? We pass full fields via patch endpoint normally,
    # but here we’ll set priority=-1 and duration=-1 and status=-1 by re-reading from DB would be cleaner.
    # We'll do a small re-read to keep C accurate.)
    conn = db_conn()
    t = conn.execute(
        "SELECT priority, deadline, start_time, duration, status FROM tasks WHERE id=?",
        (task_id,),
    ).fetchone()
    conn.close()

    lib.tm_update_task(
        int(task_id),
        int(t["priority"]),
        str(t["deadline"]).encode("utf-8"),
        str(t["start_time"]).encode("utf-8"),
        int(t["duration"]),
        int(t["status"]),
    )

    return {"ok": True}


# -----------------------------
# Run (dev)
# -----------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)