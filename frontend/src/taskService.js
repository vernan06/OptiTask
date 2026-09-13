const STORAGE_KEY = "optitask.tasks";
const CATEGORIES = ["work", "study", "personal", "home", "finance", "health", "general"];
const WEEKDAYS = {
  monday: 0, mon: 0, tuesday: 1, tue: 1, tues: 1, wednesday: 2, wed: 2,
  thursday: 3, thu: 3, thur: 3, thurs: 3, friday: 4, fri: 4,
  saturday: 5, sat: 5, sunday: 6, sun: 6,
};

function todayDate() {
  const date = new Date();
  date.setHours(0, 0, 0, 0);
  return date;
}

function todayIso() {
  return todayDate().toISOString().slice(0, 10);
}

function readTasks() {
  try {
    const stored = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(stored) ? stored : [];
  } catch {
    return [];
  }
}

function writeTasks(tasks) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function nextId(tasks) {
  return tasks.reduce((highest, task) => Math.max(highest, Number(task.id) || 0), 0) + 1;
}

function sortTasks(tasks) {
  return [...tasks].sort((a, b) =>
    Number(a.status) - Number(b.status) ||
    Number(a.priority) - Number(b.priority) ||
    String(a.deadline || "").localeCompare(String(b.deadline || "")) ||
    String(a.start_time || "").localeCompare(String(b.start_time || ""))
  );
}

function parseDate(text) {
  const lower = text.toLowerCase();
  const today = todayDate();
  if (lower.includes("yesterday")) return "__PAST__";
  if (lower.includes("today")) return todayIso();
  if (/\b(?:tomorrow|tmr|tmrw|tommow)\b/.test(lower)) {
    const date = new Date(today);
    date.setDate(date.getDate() + 1);
    return date.toISOString().slice(0, 10);
  }

  const days = lower.match(/\bin\s+(\d+)\s+days?\b/);
  if (days) {
    const date = new Date(today);
    date.setDate(date.getDate() + Number(days[1]));
    return date.toISOString().slice(0, 10);
  }

  for (const [name, weekday] of Object.entries(WEEKDAYS)) {
    const nextWeek = new RegExp(`\\bnext\\s+week\\s+${name}\\b`).test(lower);
    const nextDay = new RegExp(`\\b(?:next\\s+)?${name}\\b`).test(lower);
    if (nextWeek || nextDay) {
      const ahead = (weekday - today.getDay() + 6) % 7 + 1 + (nextWeek ? 7 : 0);
      const date = new Date(today);
      date.setDate(date.getDate() + ahead);
      return date.toISOString().slice(0, 10);
    }
  }
  return todayIso();
}

function parseTime(text) {
  const clock = text.match(/\b([01]?\d|2[0-3]):([0-5]\d)\b/);
  if (clock) return `${String(Number(clock[1])).padStart(2, "0")}:${clock[2]}`;
  const meridiem = text.toLowerCase().match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b/);
  if (!meridiem) return "";
  let hours = Number(meridiem[1]);
  const minutes = Number(meridiem[2] || 0);
  if (meridiem[3] === "pm" && hours !== 12) hours += 12;
  if (meridiem[3] === "am" && hours === 12) hours = 0;
  return `${String(hours).padStart(2, "0")}:${String(minutes).padStart(2, "0")}`;
}

function parseDuration(text) {
  const hours = text.match(/\b(\d+)\s*h(?:\s*(\d+)\s*m)?\b/i);
  if (hours) return Number(hours[1]) * 60 + Number(hours[2] || 0);
  const minutes = text.match(/\b(\d+)\s*m\b/i);
  return minutes ? Number(minutes[1]) : 30;
}

function validateDateTime(deadline, startTime) {
  if (deadline === "__PAST__") throw new Error("Cannot schedule tasks for past dates");
  if (deadline < todayIso()) throw new Error(`Cannot schedule tasks for past date (${deadline})`);
  if (deadline === todayIso() && startTime) {
    const now = new Date();
    const current = now.getHours() * 60 + now.getMinutes();
    const [hours, minutes] = startTime.split(":").map(Number);
    if (hours * 60 + minutes < current) throw new Error(`Cannot schedule tasks for past time (${startTime})`);
  }
}

export function parseCommand(text) {
  const raw = text.trim();
  const lower = raw.toLowerCase();
  const priority = Number((lower.match(/\bp([1-5])\b/) || ["", 3])[1]);
  const deadline = parseDate(raw);
  const startTime = parseTime(raw);
  validateDateTime(deadline, startTime);

  const category = CATEGORIES.find((item) => new RegExp(`\\b${item}\\b`, "i").test(raw)) || "general";
  const name = raw
    .replace(/\bp[1-5]\b/gi, " ")
    .replace(/\b\d+\s*h(?:\s*\d+\s*m)?\b/gi, " ")
    .replace(/\b\d+\s*m\b/gi, " ")
    .replace(/\b(today|tomorrow|tmr|tmrw|tommow|yesterday)\b/gi, " ")
    .replace(/\bin\s+\d+\s+days?\b/gi, " ")
    .replace(/\bnext\s+week\s+\w+\b|\bnext\s+\w+\b/gi, " ")
    .replace(/\b(?:monday|mon|tuesday|tue|tues|wednesday|wed|thursday|thu|thur|thurs|friday|fri|saturday|sat|sunday|sun)\b/gi, " ")
    .replace(/\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\b\d{1,2}(?::\d{2})?\s*(?:am|pm)\b/gi, " ")
    .replace(/\b(for|at|to|called|named)\b/gi, " ")
    .replace(new RegExp(`\\b(?:${CATEGORIES.join("|")})\\b`, "gi"), " ")
    .replace(/\s+/g, " ")
    .trim();

  if (!name) throw new Error("Add a task name to that command");
  return { name, category, priority, deadline, start_time: startTime, duration: Math.max(15, parseDuration(raw)), status: 0 };
}

export function listTasks() {
  return sortTasks(readTasks());
}

export function createTask(input) {
  const tasks = readTasks();
  const task = {
    id: nextId(tasks),
    name: input.name.trim(),
    category: input.category || "general",
    priority: Number(input.priority || 3),
    deadline: input.deadline || todayIso(),
    start_time: input.start_time || "",
    duration: Number(input.duration || 30),
    status: Number(input.status || 0),
  };
  validateDateTime(task.deadline, task.start_time);
  writeTasks([...tasks, task]);
  return task;
}

export function updateTask(id, changes) {
  const tasks = readTasks();
  const index = tasks.findIndex((task) => Number(task.id) === Number(id));
  if (index < 0) throw new Error("Task not found");
  const updated = { ...tasks[index], ...changes };
  writeTasks(tasks.map((task, taskIndex) => (taskIndex === index ? updated : task)));
  return updated;
}

export function deleteTask(id) {
  const tasks = readTasks();
  writeTasks(tasks.filter((task) => Number(task.id) !== Number(id)));
}

export function ghostSchedule(date, sourceTasks = readTasks()) {
  const tasks = sourceTasks;
  const unscheduled = tasks
    .filter((task) => task.status === 0 && !task.start_time)
    .sort((a, b) => a.priority - b.priority || String(a.deadline).localeCompare(String(b.deadline)))
    .slice(0, 6);
  const occupied = tasks
    .filter((task) => task.status === 0 && task.deadline === date && task.start_time)
    .map((task) => {
      const [hours, minutes] = task.start_time.split(":").map(Number);
      const start = hours * 60 + minutes;
      return [start, start + Math.max(Number(task.duration) || 0, 0)];
    });
  const suggestions = [];
  for (const task of unscheduled) {
    const duration = Math.max(Number(task.duration) || 30, 15);
    let slot = 480;
    while (slot + duration <= 1200 && occupied.some(([start, end]) => slot < end && slot + duration > start)) slot += 30;
    suggestions.push({ task_id: task.id, name: task.name, priority: task.priority, duration, suggested_time: `${String(Math.floor(slot / 60)).padStart(2, "0")}:${String(slot % 60).padStart(2, "0")}`, deadline: date });
    occupied.push([slot, slot + duration]);
  }
  return suggestions;
}

function taskList(tasks) {
  return tasks.length ? tasks.slice(0, 10).map((task) => `#${task.id}: ${task.name} (P${task.priority})`).join("\n") : "Your schedule is clear! No active tasks.";
}

export function assistantMessage(text) {
  const lower = text.toLowerCase().trim();
  const tasks = listTasks().filter((task) => task.status === 0);
  if (/^(hi|hello|hey)\b/.test(lower)) return { response: "Hey! I'm OptiTask. How can I help?" };
  if (/how are you/.test(lower)) return { response: "Running optimally! How can I help?" };
  if (/thank/.test(lower)) return { response: "You're welcome!" };
  if (/^help$|what can you do/.test(lower)) return { response: "I can add tasks, show your schedule, mark tasks done, delete tasks, and give productivity advice." };
  if (/what.*(time|date)|^time$/.test(lower)) return { response: `Today is ${new Date().toLocaleString(undefined, { dateStyle: "full", timeStyle: "short" })}.` };
  if (/(show|list|what).*(task|schedule|agenda|to.?do)/.test(lower)) return { response: `Here's your schedule:\n${taskList(tasks)}` };

  const complete = lower.match(/(?:mark|complete|finish)\s+(?:task\s+)?#?(\d+)/);
  if (complete) {
    updateTask(Number(complete[1]), { status: 1 });
    return { action: "complete_task", response: `Marked task #${complete[1]} as done!` };
  }
  const remove = lower.match(/(?:delete|remove|cancel)\s+(?:task\s+)?#?(\d+)/);
  if (remove) {
    deleteTask(Number(remove[1]));
    return { action: "delete_task", response: `Deleted task #${remove[1]}.` };
  }
  if (/\b(add|create|remind me to|i need to|schedule)\b/.test(lower)) {
    const taskText = text.replace(/^(?:add|create|schedule)\s+(?:a\s+)?(?:new\s+)?(?:task|meeting|reminder|event)?\s*/i, "").replace(/^remind me to\s+/i, "");
    const task = createTask(parseCommand(taskText));
    return { action: "add_task", response: `Done! Added '${task.name}' for ${task.deadline}.` };
  }
  if (/priorit|urgent/.test(lower)) return { response: "Use the Eisenhower Matrix: do urgent and important work now, schedule important work, delegate urgent distractions, and skip the rest." };
  if (/productiv|focus|procrastinat/.test(lower)) return { response: "Try a 25-minute focus sprint, silence notifications, and start with the smallest visible next action." };
  return { response: "I can add tasks, show your schedule, mark tasks done, delete tasks, or offer productivity advice. Try 'add study tomorrow 2pm' or 'show my tasks'." };
}
