"""
services/chat_engine.py
-----------------------
AI chat engine using Groq (free tier, Llama 3.3 70B).
Falls back to rule-based responses if Groq is unavailable.
"""

import os
import json
import httpx
from typing import Optional

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"

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


def _rule_based_reply(message: str, analytics: dict) -> Optional[str]:
    """Simple rule-based fallback when Groq is unavailable."""
    msg = message.lower()
    kpis = analytics.get("kpis", {})
    breakdown = analytics.get("category_breakdown", [])
    merchants = analytics.get("top_merchants", [])

    total_spend = kpis.get("total_spend", 0)
    total_credit = kpis.get("total_credit", 0)

    if any(w in msg for w in ["spend", "spent", "total", "how much"]):
        return f"You've spent ₹{total_spend:,.0f} this month across {kpis.get('transaction_count', 0)} transactions. Your average transaction is ₹{kpis.get('avg_transaction', 0):,.0f}."

    if any(w in msg for w in ["save", "saving", "savings"]):
        net = total_credit - total_spend
        if net > 0:
            return f"You've saved ₹{net:,.0f} this month (₹{total_credit:,.0f} income minus ₹{total_spend:,.0f} expenses). That's great!"
        else:
            return f"You're overspending by ₹{abs(net):,.0f} this month. Income: ₹{total_credit:,.0f}, Expenses: ₹{total_spend:,.0f}. Try cutting back on non-essential categories."

    if any(w in msg for w in ["top", "highest", "most"]):
        if merchants:
            top = merchants[0]
            return f"Your highest expense is at {top['merchant']} — ₹{top['total']:,.0f} across {top['count']} transactions."
        return "I don't have enough data to identify your top expenses yet."

    if any(w in msg for w in ["food", "eating", "restaurant"]):
        food = next((b for b in breakdown if b["category"] == "food"), None)
        if food:
            return f"You spent ₹{food['total']:,.0f} on food ({food['percentage']}% of total spending). That's {food['count']} transactions averaging ₹{food['avg_transaction']:,.0f} each."
        return "No food expenses found this month."

    if any(w in msg for w in ["cut", "reduce", "cheap", "budget"]):
        if breakdown:
            top_cat = breakdown[0]
            return f"Your biggest category is {top_cat['category']} at ₹{top_cat['total']:,.0f} ({top_cat['percentage']}%). Focus on reducing spending here for the biggest impact."
        return "I'd need to see your spending breakdown to suggest where to cut costs."

    if any(w in msg for w in ["hello", "hi", "hey"]):
        return "Hi! I'm Pawket, your finance assistant. Ask me about your spending, savings, or budget!"

    if any(w in msg for w in ["who", "what are you"]):
        return "I'm Pawket — your personal finance assistant. I can analyze your spending, track your budget, and help you save money."

    return None


async def get_chat_reply(
    message: str,
    analytics: dict,
    month: str,
    history: list = None,
    user_profile: dict = None,
) -> str:
    """Get a chat reply using Groq API, with rule-based fallback."""
    # Try rule-based first for common queries
    rule_reply = _rule_based_reply(message, analytics)
    if rule_reply:
        return rule_reply

    # If no Groq key, return generic helpful response
    if not GROQ_API_KEY:
        return "I can help with basic questions about your spending and budget. For detailed analysis, please check the Insights section above."

    context = _build_context(analytics, month, user_profile)

    messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n\nUser's financial data:\n" + context}]

    # Add conversation history
    if history:
        for h in history[-8:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("text", "")})

    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                GROQ_BASE_URL,
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": GROQ_MODEL,
                    "messages": messages,
                    "max_tokens": 256,
                    "temperature": 0.7,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"[CHAT] Groq API error: {e}")
        return "I'm having trouble connecting right now. Please try again in a moment."
