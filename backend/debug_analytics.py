import requests, json
from datetime import datetime
from collections import defaultdict

API = 'https://pawket-gwqd.onrender.com'
r = requests.post(f'{API}/auth/request-otp', json={'phone': '+917377044562'})
msg = r.json().get('message','')
otp = msg.split('[DEV:')[1].split(']')[0].strip()
r = requests.post(f'{API}/auth/verify-otp', json={'phone': '+917377044562', 'otp': otp})
token = r.json().get('token')
headers = {'Authorization': f'Bearer {token}'}

r = requests.get(f'{API}/analytics/transactions?month=2026-09&limit=50', headers=headers, timeout=30)
data = r.json()
txns = data.get('transactions', [])
print(f"Total txns: {data.get('total')}")

debits = [t for t in txns if t.get('transaction_type') == 'debit' and t.get('amount')]
credits = [t for t in txns if t.get('transaction_type') == 'credit' and t.get('amount')]
print(f"Debits: {len(debits)}, Credits: {len(credits)}")

debit_amounts = [t['amount'] for t in debits]
sorted_amounts = sorted(debit_amounts)
n = len(sorted_amounts)
print(f"n={n}, sorted={sorted_amounts}")

# Median calc - same as analytics.py
median = (
    (sorted_amounts[n//2 - 1] + sorted_amounts[n//2]) / 2
    if n % 2 == 0 and n > 0
    else sorted_amounts[n//2] if n > 0 else 0
)
print(f"Median: {median}")

# Daily trend
daily = defaultdict(float)
daily_cat = defaultdict(str)
daily_cat_amount = defaultdict(float)
for t in debits:
    received = t.get('received_at')
    if received:
        dt = datetime.fromisoformat(received)
        day = dt.strftime('%Y-%m-%d')
        daily[day] += t['amount']
        cat = t.get('final_category') or 'others'
        if t['amount'] > daily_cat_amount.get(day, 0):
            daily_cat[day] = cat
            daily_cat_amount[day] = t['amount']

daily_trend = [
    {"date": d, "amount": round(amt, 2), "category": daily_cat[d]}
    for d, amt in sorted(daily.items())
]
print(f"Daily trend days: {len(daily_trend)}")

# Category breakdown
category_totals = defaultdict(float)
category_counts = defaultdict(int)
for t in debits:
    cat = t.get('final_category') or 'others'
    category_totals[cat] += t['amount']
    category_counts[cat] += 1

total_spend = sum(debit_amounts)
for cat, total in sorted(category_totals.items(), key=lambda x: -x[1]):
    pct = round(total / total_spend * 100, 1) if total_spend else 0
    print(f"  {cat}: {total:.0f} ({pct}%)")

print("\nAll checks passed - no crash!")
