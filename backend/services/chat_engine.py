"""
services/chat_engine.py
-----------------------
AI chat engine using Groq (free tier, Llama 3.3 70B).
Falls back to rule-based responses if Groq is unavailable.
"""

import os
import re
import json
import httpx
from typing import Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

SYSTEM_PROMPT = """You are Pawket, a friendly and smart personal finance assistant for an Indian user.
You have access to their actual financial data for the current month. Use it to give specific, actionable advice.

Rules:
- Always use Indian Rupee (₹) when mentioning amounts
- Be concise — 2-3 sentences max per answer
- Give specific numbers from their data, not generic advice
- Be encouraging but honest about overspending
- If asked about something not in their data, say so honestly
- Never make up numbers or data you don't have
- Use simple language, avoid financial jargon"""


def _build_context(analytics: dict, month: str, user_profile: dict = None) -> str:
    """Build a financial context string from analytics data."""
    kpis = analytics.get("kpis", {})
    breakdown = analytics.get("category_breakdown", [])
    merchants = analytics.get("top_merchants", [])

    ctx_parts = [
        f"Month: {month}",
        f"Total spent: ₹{kpis.get('total_spend', 0):,.0f}",
        f"Total received: ₹{kpis.get('total_credit', 0):,.0f}",
        f"Transaction count: {kpis.get('transaction_count', 0)}",
        f"Average transaction: ₹{kpis.get('avg_transaction', 0):,.0f}",
        f"Largest transaction: ₹{kpis.get('largest_transaction', 0):,.0f}",
        f"Median transaction: ₹{kpis.get('median_transaction', 0):,.0f}",
    ]

    if kpis.get("most_spent_category"):
        ctx_parts.append(f"Most spent category: {kpis['most_spent_category']} (₹{kpis.get('most_spent_amount', 0):,.0f})")

    if breakdown:
        ctx_parts.append("\nCategory breakdown:")
        for b in breakdown[:8]:
            ctx_parts.append(f"  - {b['category']}: ₹{b['total']:,.0f} ({b['percentage']}%, {b['count']} txns)")

    if merchants:
        ctx_parts.append("\nTop merchants:")
        for m in merchants[:5]:
            ctx_parts.append(f"  - {m['merchant']}: ₹{m['total']:,.0f} ({m['count']}x)")

    if user_profile:
        if user_profile.get("name"):
            ctx_parts.append(f"\nUser: {user_profile['name']}")
        if user_profile.get("financial_goal"):
            ctx_parts.append(f"Financial goal: {user_profile['financial_goal']}")

    return "\n".join(ctx_parts)


def _has_words(msg, words):
    """Word-boundary match so 'hi' doesn't hit 'this'/'which' and 'emi' doesn't hit 'premium'."""
    return any(re.search(r"\b" + re.escape(w) + r"\b", msg) for w in words)


def _prev_month_label(month: Optional[str]) -> str:
    if not month or len(month) < 7:
        return "the previous month"
    try:
        y, m = int(month[:4]), int(month[5:7])
        prev = (y - 1, 12) if m == 1 else (y, m - 1)
        return f"{prev[0]:04d}-{prev[1]:02d}"
    except ValueError:
        return "the previous month"


_CATEGORY_KEYWORDS = {
    "food":       ["food", "eating", "restaurant", "restaurants", "dining", "swiggy", "zomato", "lunch", "dinner"],
    "transport":  ["transport", "uber", "ola", "petrol", "fuel", "metro", "irctc", "train", "flight", "rapido"],
    "shopping":   ["shopping", "amazon", "flipkart", "myntra"],
    "health":     ["health", "medical", "pharmacy", "apollo", "pharmeasy", "netmeds"],
    "emi":        ["emi", "loan", "instalment", "installment"],
    "investment": ["investment", "investing", "zerodha", "groww", "sip", "mutual fund"],
    "utilities":  ["utilities", "utility", "electricity", "broadband", "recharge", "netflix", "spotify", "airtel", "jio"],
    "education":  ["education", "course", "udemy", "coursera", "tuition", "school"],
    "transfer":   ["transfer"],
}


def _category_reply(breakdown, cat):
    b = next((x for x in breakdown if x.get("category") == cat), None)
    if not b:
        return None
    avg = b.get("avg_transaction") or (b["total"] / b["count"] if b.get("count") else 0)
    return (f"You spent ₹{b['total']:,.0f} on {cat} ({b['percentage']}% of your total spending) "
            f"across {b['count']} transactions, averaging ₹{avg:,.0f} each.")


def _rule_based_reply(message: str, analytics: dict, month: str = None,
                      prev_analytics: dict = None) -> Optional[str]:
    """Rule-based answers — specific intents first, generic spend last."""
    msg = message.lower()
    kpis = analytics.get("kpis", {}) if analytics else {}
    breakdown = analytics.get("category_breakdown", []) if analytics else []
    merchants = analytics.get("top_merchants", []) if analytics else []

    total_spend = kpis.get("total_spend", 0)
    total_credit = kpis.get("total_credit", 0)

    # 1. Greetings / intro (word-boundary safe)
    if _has_words(msg, ["hello", "hi", "hey"]):
        return "Hi! I'm Pawket, your finance assistant. Ask me about your spending, savings, or budget!"
    if re.search(r"\bwho are you\b|\bwhat are you\b", msg):
        return ("I'm Pawket — your personal finance assistant. I can analyze your spending, "
                "track your budget, and help you save money.")

    # 2. Specific category questions (food, emi, utilities, ...)
    for cat, kws in _CATEGORY_KEYWORDS.items():
        if _has_words(msg, kws) or _has_words(msg, [cat]):
            reply = _category_reply(breakdown, cat)
            return reply or f"No {cat} expenses found this month."
    for b in breakdown:
        if _has_words(msg, [b.get("category", "")]):
            reply = _category_reply(breakdown, b["category"])
            if reply:
                return reply

    # 3. Cut / reduce / budget / tip questions → biggest category advice
    if _has_words(msg, ["cut", "reduce", "reducing", "cheaper", "cheap", "budget", "tip", "tips",
                        "advice", "suggest", "improve"]):
        if breakdown:
            top_cat = breakdown[0]
            return (f"Your biggest category is {top_cat['category']} at ₹{top_cat['total']:,.0f} "
                    f"({top_cat['percentage']}%). Focus on reducing spending here for the biggest impact.")
        return "I'd need to see your spending breakdown to suggest where to cut costs."

    # 4. Top / highest / most — category or merchant
    if _has_words(msg, ["top", "highest", "most", "biggest", "largest"]):
        if "categor" in msg or "spending" in msg:
            if breakdown:
                top = breakdown[0]
                return (f"Your biggest category is {top['category']} at ₹{top['total']:,.0f} "
                        f"({top['percentage']}% of spending, {top['count']} transactions).")
            return "I don't have a spending breakdown for this month yet."
        if merchants:
            t = merchants[0]
            return f"Your highest expense is at {t['merchant']} — ₹{t['total']:,.0f} across {t['count']} transactions."
        return "I don't have enough data to identify your top expenses yet."

    # 5. Overspending / savings
    overspending = bool(re.search(r"\boverspend", msg)) or _has_words(msg, ["over budget", "running over"])
    saving = _has_words(msg, ["save", "saving", "savings", "saved"])
    if overspending or saving:
        net = total_credit - total_spend
        top_line = ""
        if breakdown:
            top_line = f" Your biggest pressure point is {breakdown[0]['category']} at ₹{breakdown[0]['total']:,.0f}."
        if overspending:
            if net >= 0:
                return (f"Overall you're okay: income ₹{total_credit:,.0f} vs spending ₹{total_spend:,.0f} "
                        f"so far — net +₹{net:,.0f}.{top_line}")
            return (f"You're overspending by ₹{abs(net):,.0f} this month — income ₹{total_credit:,.0f}, "
                    f"expenses ₹{total_spend:,.0f}.{top_line} Trim that category first.")
        if net > 0:
            return (f"You've saved ₹{net:,.0f} this month (₹{total_credit:,.0f} income minus "
                    f"₹{total_spend:,.0f} expenses). That's great!")
        return (f"You're overspending by ₹{abs(net):,.0f} this month. Income: ₹{total_credit:,.0f}, "
                f"Expenses: ₹{total_spend:,.0f}. Try cutting back on non-essential categories.")

    # 6. Month-over-month compare (prev analytics supplied by the router)
    if _has_words(msg, ["compare", "versus", "vs", "last month", "previous month",
                        "earlier", "month over month"]) or "than last" in msg:
        prev_label = _prev_month_label(month)
        prev_total = ((prev_analytics or {}).get("kpis", {}) or {}).get("total_spend", 0)
        if not prev_total:
            return f"I don't have spending data for {prev_label} to compare against."
        change = total_spend - prev_total
        pct = abs(change) / prev_total * 100
        direction = "up" if change >= 0 else "down"
        return (f"{month or 'This month'}: ₹{total_spend:,.0f} vs {prev_label}: ₹{prev_total:,.0f} — "
                f"you spent {direction} {pct:.0f}% (₹{abs(change):,.0f} {'more' if change >= 0 else 'less'}).")

    # 7. Generic spend/total — LAST so it can't swallow specific questions
    if _has_words(msg, ["spend", "spent", "total", "how much", "transaction"]):
        return (f"You've spent ₹{total_spend:,.0f} this month across "
                f"{kpis.get('transaction_count', 0)} transactions. "
                f"Your average transaction is ₹{kpis.get('avg_transaction', 0):,.0f}.")

    return None


def _offline_summary(analytics: dict, month: str) -> str:
    """Useful data snapshot when the LLM is unavailable — never a dead-end error."""
    kpis = (analytics or {}).get("kpis", {})
    if not kpis:
        return f"I couldn't load your {month or ''} data right now. Please try again in a moment."
    breakdown = (analytics or {}).get("category_breakdown", []) or []
    merchants = (analytics or {}).get("top_merchants", []) or []
    spend = kpis.get("total_spend", 0)
    credit = kpis.get("total_credit", 0)
    count = kpis.get("transaction_count", 0)
    avg = kpis.get("avg_transaction", 0)

    parts = [f"Quick {month or 'monthly'} snapshot: you spent ₹{spend:,.0f} across {count} transactions "
             f"(average ₹{avg:,.0f})."]
    if breakdown:
        top = breakdown[0]
        parts.append(f"Biggest category: {top['category']} at ₹{top['total']:,.0f} ({top['percentage']}%).")
    if merchants:
        m0 = merchants[0]
        parts.append(f"Top merchant: {m0['merchant']} (₹{m0['total']:,.0f}, {m0['count']}x).")
    if credit:
        net = credit - spend
        parts.append(f"You received ₹{credit:,.0f} — net {'savings' if net >= 0 else 'shortfall'} "
                     f"₹{abs(net):,.0f}.")
    if breakdown:
        parts.append(f"Tip: trimming {breakdown[0]['category']} would help the most.")
    parts.append("(Pawket AI is briefly unavailable, so here's a quick data summary instead.)")
    return " ".join(parts)


async def get_chat_reply(
    message: str,
    analytics: dict,
    month: str,
    history: list = None,
    user_profile: dict = None,
    prev_analytics: dict = None,
) -> str:
    """Get a chat reply using Groq API, with rule-based fallback."""
    # Try rule-based first for common queries
    rule_reply = _rule_based_reply(message, analytics, month=month, prev_analytics=prev_analytics)
    if rule_reply:
        return rule_reply

    # If no Groq key, return a useful data snapshot
    if not GROQ_API_KEY:
        return _offline_summary(analytics, month)

    context = _build_context(analytics, month, user_profile)

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nUser's financial data:\n" + context}]

    # Add conversation history
    if history:
        for h in history[-8:]:
            raw_role = h.get("role", "user")
            if raw_role in ("bot", "assistant"):
                role = "assistant"
            else:
                role = "user"
            content = h.get("text") or h.get("content") or ""
            if content:
                messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                GROQ_BASE_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 1024,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = (data["choices"][0]["message"].get("content") or "").strip()
            if not content:
                # reasoning models can exhaust max_tokens on reasoning alone
                return _offline_summary(analytics, month)
            return content
    except Exception as e:
        print(f"[CHAT] Groq API error: {e}")
        return _offline_summary(analytics, month)
