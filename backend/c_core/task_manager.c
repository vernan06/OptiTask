#include "task_manager.h"
#include <stdlib.h>
#include <string.h>

typedef struct {
  int id;
  char* name;
  char* category;
  int priority;
  char* deadline;     // YYYY-MM-DD
  char* start_time;   // HH:MM
  int duration_mins;
  int status;         // 0 active, 1 done
} Task;

static Task* g_tasks = NULL;
static int g_count = 0;
static int g_cap = 0;
static int g_next_id = 1;

static char* tm_strdup(const char* s) {
  if (!s) {
    char* z = (char*)malloc(1);
    if (z) z[0] = '\0';
    return z;
  }
  size_t n = strlen(s);
  char* out = (char*)malloc(n + 1);
  if (!out) return NULL;
  memcpy(out, s, n + 1);
  return out;
}

static void tm_free_task(Task* t) {
  if (!t) return;
  free(t->name);
  free(t->category);
  free(t->deadline);
  free(t->start_time);
  t->name = t->category = t->deadline = t->start_time = NULL;
}

static void tm_ensure_cap(int need) {
  if (g_cap >= need) return;
  int new_cap = g_cap == 0 ? 16 : g_cap * 2;
  while (new_cap < need) new_cap *= 2;
  Task* nt = (Task*)realloc(g_tasks, sizeof(Task) * new_cap);
  if (!nt) return; // OOM: leave as-is (caller will fail later gracefully)
  g_tasks = nt;
  g_cap = new_cap;
}

static int tm_find_index_by_id(int id) {
  for (int i = 0; i < g_count; i++) {
    if (g_tasks[i].id == id) return i;
  }
  return -1;
}

TM_API void tm_init(void) {
  // nothing special; lazy init
  if (!g_tasks) {
    g_tasks = NULL;
    g_count = 0;
    g_cap = 0;
    g_next_id = 1;
  }
}

TM_API void tm_reset(void) {
  for (int i = 0; i < g_count; i++) {
    tm_free_task(&g_tasks[i]);
  }
  free(g_tasks);
  g_tasks = NULL;
  g_count = 0;
  g_cap = 0;
  g_next_id = 1;
}

static int tm_add_internal(
  int id,
  const char* name,
  const char* category,
  int priority,
  const char* deadline,
  const char* start_time,
  int duration_mins,
  int status,
  int force_id
) {
  if (!name || strlen(name) == 0) return -1;

  tm_ensure_cap(g_count + 1);
  if (g_cap < g_count + 1) return -1;

  Task t;
  memset(&t, 0, sizeof(Task));

  if (force_id) {
    t.id = id;
    if (id >= g_next_id) g_next_id = id + 1;
  } else {
    t.id = g_next_id++;
  }

  t.name = tm_strdup(name);
  t.category = tm_strdup(category ? category : "general");
  t.priority = priority;
  t.deadline = tm_strdup(deadline ? deadline : "");
  t.start_time = tm_strdup(start_time ? start_time : "");
  t.duration_mins = duration_mins;
  t.status = status;

  if (!t.name || !t.category || !t.deadline || !t.start_time) {
    tm_free_task(&t);
    return -1;
  }

  g_tasks[g_count++] = t;
  return t.id;
}

TM_API int tm_add_task(
  const char* name,
  const char* category,
  int priority,
  const char* deadline,
  const char* start_time,
  int duration_mins,
  int status
) {
  return tm_add_internal(0, name, category, priority, deadline, start_time, duration_mins, status, 0);
}

TM_API int tm_add_task_with_id(
  int id,
  const char* name,
  const char* category,
  int priority,
  const char* deadline,
  const char* start_time,
  int duration_mins,
  int status
) {
  if (id <= 0) return -1;

  // If already exists, we update it instead of duplicating.
  int idx = tm_find_index_by_id(id);
  if (idx >= 0) {
    tm_update_task(id, priority, deadline, start_time, duration_mins, status);
    if (id >= g_next_id) g_next_id = id + 1;
    return id;
  }

  return tm_add_internal(id, name, category, priority, deadline, start_time, duration_mins, status, 1);
}

TM_API int tm_update_task(
  int id,
  int priority,
  const char* deadline,
  const char* start_time,
  int duration_mins,
  int status
) {
  int idx = tm_find_index_by_id(id);
  if (idx < 0) return 0;

  Task* t = &g_tasks[idx];

  if (priority != -1) t->priority = priority;
  if (duration_mins != -1) t->duration_mins = duration_mins;
  if (status != -1) t->status = status;

  if (deadline != NULL) {
    free(t->deadline);
    t->deadline = tm_strdup(deadline);
    if (!t->deadline) t->deadline = tm_strdup("");
  }

  if (start_time != NULL) {
    free(t->start_time);
    t->start_time = tm_strdup(start_time);
    if (!t->start_time) t->start_time = tm_strdup("");
  }

  return 1;
}

TM_API int tm_delete_task(int id) {
  int idx = tm_find_index_by_id(id);
  if (idx < 0) return 0;

  tm_free_task(&g_tasks[idx]);

  // swap-delete
  g_tasks[idx] = g_tasks[g_count - 1];
  g_count--;

  return 1;
}