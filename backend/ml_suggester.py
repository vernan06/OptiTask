from typing import Dict, Tuple

class MLSuggester:
    def __init__(self):
        self.category_keywords = {
            "work": ["meeting", "client", "email", "report", "presentation", "project", "office", "call"],
            "study": ["assignment", "exam", "study", "lecture", "lab", "homework", "paper", "thesis"],
            "personal": ["gym", "doctor", "family", "shopping", "health", "friend", "travel"],
            "finance": ["bill", "payment", "invoice", "tax", "bank", "budget", "salary"],
            "home": ["clean", "laundry", "repair", "maintenance", "groceries", "cook"],
            "urgent": ["urgent", "asap", "immediately", "critical", "emergency", "now"],
        }

        self.priority_keywords = {
            1: ["urgent", "asap", "critical", "emergency", "immediately", "today"],
            2: ["important", "soon", "this week", "deadline"],
            3: ["normal", "regular", "routine"],
            4: ["later", "optional", "whenever"],
            5: ["someday", "eventually", "nice to have"],
        }

    def suggest_category(self, text: str) -> Tuple[str, float]:
        t = (text or "").lower().strip()
        if not t:
            return ("general", 0.3)

        scores = {}
        for cat, kws in self.category_keywords.items():
            score = sum(1 for k in kws if k in t)
            if score:
                scores[cat] = score

        if not scores:
            return ("general", 0.35)

        best = max(scores, key=scores.get)
        conf = min(scores[best] / 3.0, 1.0)
        return (best, conf)

    def suggest_priority(self, text: str, date: str = "", time: str = "") -> Tuple[int, float]:
        combined = f"{(text or '').lower()} {(date or '').lower()} {(time or '').lower()}".strip()
        if not combined:
            return (3, 0.5)

        scores = {}
        for p, kws in self.priority_keywords.items():
            score = sum(2 for k in kws if k in combined)
            if score:
                scores[p] = score

        if not scores:
            return (3, 0.55)

        best = min(scores, key=lambda p: (p, -scores[p]))
        conf = min(scores[best] / 6.0, 1.0)
        return (best, conf)

    def get_smart_suggestions(self, text: str, date: str = "", time: str = "") -> Dict:
        cat, cat_conf = self.suggest_category(text)
        pri, pri_conf = self.suggest_priority(text, date, time)

        return {
            "suggested_category": cat,
            "category_confidence": round(cat_conf, 2),
            "suggested_priority": pri,
            "priority_confidence": round(pri_conf, 2),
            "explanation": "Auto-suggested from keywords in your task title (you can override anytime).",
        }

ml_suggester = MLSuggester()