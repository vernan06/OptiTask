#pragma once

#ifdef _WIN32
  #define TM_API __declspec(dllexport)
#else
  #define TM_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

TM_API void tm_init(void);
TM_API void tm_reset(void);

TM_API int tm_add_task(
  const char* name,
  const char* category,
  int priority,
  const char* deadline,
  const char* start_time,
  int duration_mins,
  int status
);

TM_API int tm_add_task_with_id(
  int id,
  const char* name,
  const char* category,
  int priority,
  const char* deadline,
  const char* start_time,
  int duration_mins,
  int status
);

TM_API int tm_update_task(
  int id,
  int priority,            // -1 keep
  const char* deadline,    // NULL keep
  const char* start_time,  // NULL keep
  int duration_mins,       // -1 keep
  int status               // -1 keep
);

TM_API int tm_delete_task(int id);

#ifdef __cplusplus
}
#endif