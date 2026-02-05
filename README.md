# ⚡ OptiTask (formerly AuraTask)

**OptiTask** is a smart, AI-powered task prioritization assistant that helps you organize your day efficiently. It combines a high-performance C core for task management logic with a modern React frontend and a Python FastAPI backend integrated with a local LLM (TinyLlama) for conversational assistance.

![OptiTask UI](https://via.placeholder.com/800x450.png?text=OptiTask+Screenshot)

## 🚀 Features

- **✅ Smart Task Management**: Create, edit, and reorganize tasks with drag-and-drop.
- **🤖 AI Assistant**: Chat with OptiTask to add tasks via natural language, ask about your schedule, or get productivity tips.
  - *Hybrid Engine*: Fast pattern matching for commands + Local LLM (TinyLlama) for complex queries.
  - *Voice Control*: Speak to your assistant directly from the browser.
- **⚡ High Performance**: Core logic (sorting, prioritizing) written in C for speed.
- **📅 Smart Scheduling**: "Ghost Schedule" feature suggests optimal times for unscheduled tasks.
- **🔒 Privacy First**: All data runs locally. The LLM runs on your machine via `transformers/torch`—no API keys required.

## 🛠️ Tech Stack

- **Frontend**: React (Vite), Lucide Icons, CSS Variables (Neon/Dark Theme)
- **Backend**: Python (FastAPI), SQLite, HuggingFace Transformers (TinyLlama)
- **Core Logic**: C (ctypes integration)

---

## 📦 Installation Guide

### Prerequisites
- **Node.js** (v16+)
- **Python** (v3.8+)
- **GCC Compiler** (for Windows, usually MinGW, if you need to rebuild the C core)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/optitask.git
cd optitask
```

### 2. Backend Setup
Navigate to the backend folder and install dependencies:

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

> **Note**: The first time you run the AI assistant features, it will download the TinyLlama model (~2GB). This happens automatically.

### 3. Frontend Setup
Open a new terminal, navigate to the frontend folder:

```bash
cd frontend
npm install
```

---

## ▶️ Running the App

You need to run **both** the backend and frontend terminals simultaneously.

### Terminal 1: Backend
```bash
cd backend
python main.py
```
*Server runs at `http://127.0.0.1:8000`*

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```
*App runs at `http://localhost:5173`*

---

## 🤖 Using the AI Assistant

Click the **Bot Icon** in the bottom-right corner to open the chat.

**Voice Commands:**
- Click the microphone icon to speak.
- Examples: 
  - *"Add a meeting with Team X tomorrow at 10am"*
  - *"Remind me to buy groceries"*
  - *"What is on my schedule today?"*

**Productivity Tips:**
- Ask: *"How do I stop procrastinating?"* or *"Give me a productivity tip"*
- The assistant uses a smart fallback system to give instant advice even if the LLM is loading.

---

## 🔧 Troubleshooting

### C Core Issues
If you see errors related to `task_manager.dll` or `ctypes`, you may need to recompile the C core for your system.

1. Navigate to `backend/c_core`
2. Run `build.bat` (Windows) or compile manually:
   ```bash
   gcc -shared -o task_manager.dll task_manager.c
   ```

### LLM / AI Issues
- **"Had trouble thinking"**: This usually means the LLM failed to load (memory issue) or failed to download. Check the backend terminal logs for details.
- **Performance**: TinyLlama requires ~4GB RAM. If your system is slow, the assistant defaults to **Pattern Matching mode**, which is instant and covers all task management commands without the LLM.

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

*Built with ❤️ for productivity.*
