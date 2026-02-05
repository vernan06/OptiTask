"""OptiTask AI Assistant - Smart Pattern Matching with Optional LLM"""
import re
import os
import random
from datetime import datetime
from typing import Optional, Tuple, Dict, Any

_llm_pipeline = None
_llm_available = None
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")


def get_today():
    return datetime.now().strftime("%A, %B %d, %Y")


def get_time():
    return datetime.now().strftime("%I:%M %p")


def get_today_iso():
    return datetime.now().date().isoformat()


class PatternMatcher:
    PATTERNS = {
        # Check list_tasks FIRST to avoid false positives with "schedule"
        "list_tasks": [
            r"(?:what(?:'s| is)?|show|list|display)\s+(?:is\s+)?(?:on\s+)?(?:my\s+)?(?:tasks?|schedule|agenda|to.?do)",
            r"what.*(?:on my|do i have|is on).*(?:schedule|today|tomorrow)",
            r"^show\s+(?:my\s+)?(?:tasks?|schedule)$",
        ],
        "add_task": [
            r"^(?:add|create|set|make|put|schedule)\s+(?:a\s+)?(?:new\s+)?(?:task|meeting|reminder|event)\s+(?:for|to|called|named)?\s*(.+)",
            r"^(?:add|create|set|make)\s+(.+?)(?:\s+(?:for|to|tomorrow|today|at|on).*)?$",
            r"(?:remind me to|i need to)\s+(.+)",
        ],
        "complete_task": [
            r"(?:mark|complete|finish)\s+(?:task\s+)?[#]?(\d+)",
            r"mark\s+(?:task\s+)?[#]?(\d+)\s+(?:as\s+)?done",
        ],
        "delete_task": [
            r"(?:delete|remove|cancel)\s+(?:task\s+)?[#]?(\d+)",
        ],
        "greeting": [r"^(?:hi|hello|hey|good\s+(?:morning|afternoon|evening))(?:\s.*)?$"],
        "how_are_you": [r"how\s+are\s+you"],
        "thanks": [r"thank"],
        "help": [r"^help$", r"what can you do"],
        "time": [r"what(?:'s| is)?\s+(?:the\s+)?time"],
        "date": [r"what(?:'s| is)?\s+(?:the\s+)?date"],
    }

    RESPONSES = {
        "greeting": ["Hey! I'm OptiTask. How can I help?", "Hello! Ready to optimize your day!"],
        "how_are_you": ["Running optimally! How can I help?"],
        "thanks": ["You're welcome!", "Happy to help!"],
        "help": ["I can: Add tasks, show schedule, mark done, delete. Just talk naturally!"],
    }

    @classmethod
    def match(cls, text: str):
        text_lower = text.lower().strip()
        for intent, patterns in cls.PATTERNS.items():
            for p in patterns:
                m = re.search(p, text_lower, re.IGNORECASE)
                if m:
                    return intent, {"groups": m.groups(), "text": text}
        return None, None

    @classmethod
    def get_response(cls, intent: str) -> str:
        return random.choice(cls.RESPONSES.get(intent, ["Got it!"]))


def check_llm_available() -> bool:
    try:
        import transformers
        return True
    except ImportError:
        return False


def load_llm():
    global _llm_pipeline, _llm_available
    if _llm_available is not None:
        return _llm_pipeline
    try:
        from transformers import pipeline
        import torch
        os.makedirs(MODELS_DIR, exist_ok=True)
        print("Loading TinyLlama (this may take a few minutes on first run)...")
        print(f"Model: {MODEL_ID}")
        print(f"Cache dir: {MODELS_DIR}")
        _llm_pipeline = pipeline("text-generation", model=MODEL_ID, cache_dir=MODELS_DIR)
        _llm_available = True
        print("TinyLlama loaded successfully!")
        return _llm_pipeline
    except Exception as e:
        import traceback
        print(f"LLM loading error: {e}")
        traceback.print_exc()
        _llm_available = False
        return None


def query_llm(msg: str, ctx: str) -> str:
    pipe = load_llm()
    if not pipe:
        return "AI offline. Try 'help'!"
    try:
        today = get_today()
        time_now = get_time()
        system = f"""You are OptiTask, a brilliant and enthusiastic productivity AI assistant.
You help users manage tasks, prioritize work, and stay productive.
Today: {today}. Current time: {time_now}.
User's current tasks: {ctx or 'No active tasks'}.

Guidelines:
- Be concise but helpful (2-3 sentences max)
- Be encouraging and positive
- If asked about tasks, reference their actual task list
- For productivity advice, give actionable tips
- You can help add, complete, or organize tasks"""
        result = pipe(f"{system}\n\nUser: {msg}\nOptiTask:", max_new_tokens=150, do_sample=True, temperature=0.7)
        response = result[0]["generated_text"].split("OptiTask:")[-1].strip()
        # Clean up any artifacts
        response = response.split("User:")[0].strip()
        print(f"LLM response: {response[:100]}...")
        return response
    except Exception as e:
        import traceback
        print(f"LLM query error: {e}")
        traceback.print_exc()
        return "Had trouble thinking. Try again!"


def process_message(text: str, tasks: list = None) -> Dict[str, Any]:
    """Main entry point for chat messages. Returns action and response."""
    intent, data = PatternMatcher.match(text)
    task_ctx = ""
    if tasks:
        task_ctx = "; ".join([f"#{t.get('id', '?')}: {t.get('name', 'untitled')}" for t in tasks[:5]])

    # Handle simple intents with pattern matching (fast path)
    if intent in ["greeting", "how_are_you", "thanks", "help"]:
        return {"action": "reply", "response": PatternMatcher.get_response(intent)}

    if intent == "time":
        return {"action": "reply", "response": f"It's {get_time()} right now."}

    if intent == "date":
        return {"action": "reply", "response": f"Today is {get_today()}."}

    if intent == "add_task":
        task_desc = data["groups"][0] if data["groups"] else text
        return {"action": "add_task", "task_text": task_desc, "response": f"Got it! Adding: {task_desc}"}

    if intent == "list_tasks":
        return {"action": "list_tasks", "response": "Here's your schedule:"}

    if intent == "complete_task":
        task_id = int(data["groups"][0]) if data["groups"] else None
        return {"action": "complete_task", "task_id": task_id, "response": f"Marked task #{task_id} as done!"}

    if intent == "delete_task":
        task_id = int(data["groups"][0]) if data["groups"] else None
        return {"action": "delete_task", "task_id": task_id, "response": f"Deleted task #{task_id}."}

    # No pattern match - try LLM if available
    if check_llm_available():
        response = query_llm(text, task_ctx)
        if "trouble" not in response.lower():
            return {"action": "reply", "response": response}
    
    # Smart fallback for common questions (no LLM needed)
    text_lower = text.lower()
    
    if "priorit" in text_lower or "urgent" in text_lower:
        return {"action": "reply", "response": "Great question! Here's the Eisenhower Matrix:\n\n🔴 **Urgent + Important** → Do it NOW\n🟡 **Important, not urgent** → Schedule it\n🟠 **Urgent, not important** → Delegate if possible\n⚪ **Neither** → Skip it!\n\nFocus on what truly moves the needle. Want me to help prioritize your tasks?"}
    
    if "productiv" in text_lower or "focus" in text_lower:
        return {"action": "reply", "response": "Here are my top productivity hacks:\n\n⚡ **Eat the frog** - Start with your hardest task\n⏰ **Time blocks** - Work in 25-50 min sprints\n📵 **Deep focus** - Phone on silent, notifications off\n🧘 **Breaks matter** - 5 min rest every hour\n\nWant me to start a focus session for you?"}
    
    if "overwhelm" in text_lower or "stress" in text_lower or "too much" in text_lower:
        return {"action": "reply", "response": "I hear you! Here's how to regain control:\n\n1. 🧠 **Brain dump** - Get everything out of your head into tasks\n2. 🎯 **Pick ONE thing** - Just the next action\n3. ⏱️ **Set a 25-min timer** - Start small\n4. 🎉 **Celebrate small wins**\n\nYou've got this! What's the single most important thing right now?"}
    
    if "time" in text_lower and "manag" in text_lower:
        return {"action": "reply", "response": "Master your time with these strategies:\n\n📋 **Plan tomorrow tonight** - Wake up with purpose\n📦 **Batch similar tasks** - Email, calls, admin together\n🚫 **Learn to say no** - Protect your time\n⏰ **Fake deadlines work!** - Create urgency\n\nShall I help you block out your day?"}
    
    if "motivat" in text_lower or "procrastinat" in text_lower:
        return {"action": "reply", "response": "Struggling to start? Try these:\n\n🔥 **2-minute rule** - If it takes <2 mins, do it NOW\n🎵 **Environment matters** - Create a focus-friendly space\n🏆 **Reward yourself** - Promise a treat after completing tasks\n👥 **Accountability** - Tell someone your goal\n\nWhat task has been lingering? Let's tackle it together!"}
    
    if "hello" in text_lower or "hi" in text_lower or "hey" in text_lower:
        return {"action": "reply", "response": f"Hey there! 👋 I'm OptiTask, your productivity partner. It's {get_time()} - let's make the most of it! What can I help you with?"}
    
    # Generic fallback with more personality
    return {"action": "reply", "response": "I'm OptiTask, your productivity sidekick! 🚀\n\nI can:\n• ➕ **Add tasks** - 'Add meeting tomorrow 3pm'\n• 📋 **Show schedule** - 'What's on my plate?'\n• ✅ **Complete tasks** - 'Mark task 1 done'\n• 💡 **Give advice** - 'How to stay focused?'\n\nWhat would you like to tackle?"}

