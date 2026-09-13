# ⚡ OptiTask

**OptiTask** is a smart task prioritization assistant that runs as a single static React application. Tasks, command parsing, ghost scheduling, and assistant replies run in the browser, with data persisted locally in `localStorage`.



## 🚀 Features

- **✅ Smart Task Management**: Create, prioritize, complete, and delete tasks.
- **🤖 AI Assistant**: Chat with OptiTask to add tasks via natural language, ask about your schedule, or get productivity tips.
  - *Browser Engine*: Fast pattern matching for commands and productivity guidance without a server.
  - *Voice Control*: Speak to your assistant directly from the browser.
- **⚡ Fast and private**: No API keys, server, database, or external service is required.
- **📅 Smart Scheduling**: "Ghost Schedule" feature suggests optimal times for unscheduled tasks.
- **🔒 Privacy First**: Your tasks stay in the browser on the device where you use the app.

## 🛠️ Tech Stack

- **Frontend**: React (Vite), Lucide Icons, CSS Variables (Neon/Dark Theme)
- **Storage and logic**: Browser `localStorage` and JavaScript modules
- **Hosting**: GitHub Pages via GitHub Actions

---

## 📦 Installation Guide

### Prerequisites
- **Node.js** (v16+)
- **Node.js** (v20+ recommended)

### Clone the Repository
```bash
git clone https://github.com/yourusername/optitask.git
cd optitask
```

### Install and run

```bash
cd frontend
npm install
npm run dev
```

---

## ▶️ Running the App

There is no second backend process. The app runs at the local URL printed by Vite.

## GitHub Pages

Push to the `main` branch and `.github/workflows/deploy-pages.yml` builds `frontend` and publishes it to GitHub Pages. In repository settings, set **Pages > Build and deployment > Source** to **GitHub Actions**.

The published site is `https://vernan06.github.io/OptiTask/`.

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
- Browser speech recognition and text-to-speech depend on browser support.

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

*Built with ❤️ for productivity.*
