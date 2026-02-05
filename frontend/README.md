# 🚀 Smart Task Prioritizer

An AI-powered task management system built with **C (core data structures)**, **Python (FastAPI)**, and **React**.

## Features

- ✅ **Min-Heap Priority Queue** (C implementation)
- ✅ **Linked List** for task storage
- ✅ **AI-powered suggestions** for category and priority
- ✅ **Real-time analytics**
- ✅ **Persistent storage**
- ✅ **Modern React UI**

## Tech Stack

- **Backend Core:** C (Min-Heap + Linked List)
- **API Server:** Python FastAPI
- **Frontend:** React + Vite
- **ML:** Scikit-learn (rule-based suggestions)

## Setup Instructions

### 1. Compile C Core

```bash
cd backend/c_core
gcc -shared -o task_manager.dll task_manager.c -Wl,--out-implib,libtask_manager.a