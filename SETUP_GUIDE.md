# ⚡ OptiTask - VS Code Setup Guide

This guide is designed for **Visual Studio Code (VS Code)** users.
Everything can be done inside VS Code's integrated terminal.

---

## �️ Prerequisites

1.  **Visual Studio Code**: [Download here](https://code.visualstudio.com/)
2.  **Extensions (Install in VS Code)**:
    *   **Python** (by Microsoft)
    *   **C/C++** (by Microsoft) - *Recommended for Mac users*
3.  **System Tools**:
    *   **Python 3.8+**
    *   **Node.js LTS**

---

## 🚀 1. Windows Setup
*(No C compilation required)*

### Step 1: Open Project in VS Code
1.  Open VS Code.
2.  File > **Open Folder** > Select the `OptiTask` folder.
3.  Open the Terminal: Press `` Ctrl + ` `` (backtick).

### Step 2: Backend Setup
Copy and paste these commands into the **VS Code Terminal**:

```powershell
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
.\venv\Scripts\activate
# (You should see '(venv)' in the prompt)

# 4. Install dependencies
pip install -r requirements.txt
```

> **Note:** The heavy lifting core (`c_core/task_manager.dll`) is pre-compiled for Windows. You don't need to do anything else!

### Step 3: Frontend Setup
1.  Open a **New Terminal** (Click the `+` icon in the terminal panel).
2.  Run:

```powershell
cd frontend
npm install
```

---

## 🍎 2. macOS Setup
*(Requires a quick one-time compilation step)*

### Step 1: Open Project in VS Code
1.  Open VS Code.
2.  File > **Open Folder** > Select the `OptiTask` folder.
3.  Open the Terminal: Press `` Cmd + ` `` (backtick).

### Step 2: Backend Setup
Copy and paste these commands into the **VS Code Terminal**:

```bash
# 1. Navigate to backend
cd backend

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate it
source venv/bin/activate

# 4. Install dependencies
pip3 install -r requirements.txt
```

### Step 3: Compile C Core (Required for Mac)
Since Macs can't run the Windows DLL, you need to compile the logic once.
In the same terminal:

```bash
cd c_core
gcc -shared -o task_manager.so task_manager.c -fPIC
cd ..
```
*If this fails, ensure you have Xcode Command Line Tools installed (`xcode-select --install`).*

### Step 4: Frontend Setup
1.  Open a **New Terminal** (Click the `+` icon in the terminal panel).
2.  Run:

```bash
cd frontend
npm install
```

---

## ▶️ Running the App (Both OS)

You need **TWO** running terminals in VS Code.
Use the **Split Terminal** button (icon looks like `|\|` or right-click terminal list -> Split).

**Terminal 1 (Backend):**
```bash
cd backend
python main.py
# (Mac users: python3 main.py)
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Click the `Local: http://localhost:5173` link in the terminal to open the app!
