"""
services/auto_seed.py
---------------------
Auto-seeds test data when the database is empty (e.g. after Render restarts).
Inserts transactions directly — no ML parsing needed.
NOTE: All data is simulated — not real bank SMS. See README for details.
"""

import json
from datetime import datetime
from database.database import SessionLocal, User, Transaction

PHONE = "+917377044562"

SEED_DATA = [
    # ═══ JULY 2026 ═══
    {"text": "INR 60000 credited. Salary from TechCorp. HDFC Bank A/c XX4567 on 01-07-2026", "amount": 60000, "merchant": None, "bank": "HDFC Bank", "txn_type": "credit", "cat": "transfer", "date": "2026-07-01T09:00:00"},
    {"text": "INR 12000 debited. Home Loan EMI. HDFC Bank A/c XX4567 on 05-07-2026", "amount": 12000, "merchant": None, "bank": "HDFC Bank", "txn_type": "debit", "cat": "emi", "date": "2026-07-05T08:30:00"},
    {"text": "INR 3500 debited. Car Loan EMI - Bajaj Finserv. SBI A/c XX8901 on 05-07-2026", "amount": 3500, "merchant": None, "bank": "SBI", "txn_type": "debit", "cat": "emi", "date": "2026-07-05T08:35:00"},
    {"text": "INR 349 debited via UPI at Swiggy on 08-07-2026. HDFC Bank A/c XX4567", "amount": 349, "merchant": "Swiggy", "bank": "HDFC Bank", "txn_type": "debit", "cat": "food", "date": "2026-07-08T12:30:00"},
    {"text": "INR 520 debited at Zomato on 12-07-2026. ICICI Bank A/c XX1234", "amount": 520, "merchant": "Zomato", "bank": "ICICI Bank", "txn_type": "debit", "cat": "food", "date": "2026-07-12T20:15:00"},
    {"text": "INR 189 debited via UPI at McDonald's on 15-07-2026. HDFC Bank A/c XX4567", "amount": 189, "merchant": "McDonald's", "bank": "HDFC Bank", "txn_type": "debit", "cat": "food", "date": "2026-07-15T13:45:00"},
    {"text": "INR 650 debited at Starbucks on 20-07-2026. Axis Bank A/c XX5678", "amount": 650, "merchant": "Starbucks", "bank": "Axis Bank", "txn_type": "debit", "cat": "food", "date": "2026-07-20T17:30:00"},
    {"text": "INR 180 debited via UPI at Uber on 10-07-2026. SBI A/c XX8901", "amount": 180, "merchant": "Uber", "bank": "SBI", "txn_type": "debit", "cat": "transport", "date": "2026-07-10T18:20:00"},
    {"text": "INR 250 debited at Ola on 18-07-2026. HDFC Bank A/c XX4567", "amount": 250, "merchant": "Ola", "bank": "HDFC Bank", "txn_type": "debit", "cat": "transport", "date": "2026-07-18T09:10:00"},
    {"text": "INR 120 debited via UPI at Rapido on 25-07-2026. ICICI Bank A/c XX1234", "amount": 120, "merchant": "Rapido", "bank": "ICICI Bank", "txn_type": "debit", "cat": "transport", "date": "2026-07-25T08:00:00"},
    {"text": "INR 4999 debited at Amazon on 22-07-2026. HDFC Bank A/c XX4567", "amount": 4999, "merchant": "Amazon", "bank": "HDFC Bank", "txn_type": "debit", "cat": "shopping", "date": "2026-07-22T14:00:00"},
    {"text": "INR 1299 debited at Flipkart on 28-07-2026. Axis Bank A/c XX5678", "amount": 1299, "merchant": "Flipkart", "bank": "Axis Bank", "txn_type": "debit", "cat": "shopping", "date": "2026-07-28T11:20:00"},
    {"text": "INR 599 debited. Airtel prepaid recharge. HDFC Bank A/c XX4567 on 01-07-2026", "amount": 599, "merchant": "Airtel", "bank": "HDFC Bank", "txn_type": "debit", "cat": "utilities", "date": "2026-07-01T10:00:00"},
    {"text": "INR 1800 debited. Electricity Bill. SBI A/c XX8901 on 10-07-2026", "amount": 1800, "merchant": None, "bank": "SBI", "txn_type": "debit", "cat": "utilities", "date": "2026-07-10T10:30:00"},
    {"text": "INR 1499 debited. Jio Fiber broadband. ICICI Bank A/c XX1234 on 15-07-2026", "amount": 1499, "merchant": "Jio", "bank": "ICICI Bank", "txn_type": "debit", "cat": "utilities", "date": "2026-07-15T10:00:00"},
    {"text": "INR 850 debited at Apollo Pharmacy on 12-07-2026. HDFC Bank A/c XX4567", "amount": 850, "merchant": "Apollo", "bank": "HDFC Bank", "txn_type": "debit", "cat": "health", "date": "2026-07-12T16:40:00"},
    {"text": "INR 320 debited at PharmEasy on 25-07-2026. ICICI Bank A/c XX1234", "amount": 320, "merchant": "PharmEasy", "bank": "ICICI Bank", "txn_type": "debit", "cat": "health", "date": "2026-07-25T14:10:00"},
    {"text": "INR 2000 debited at Zerodha on 15-07-2026. Axis Bank A/c XX5678", "amount": 2000, "merchant": "Zerodha", "bank": "Axis Bank", "txn_type": "debit", "cat": "investment", "date": "2026-07-15T11:00:00"},
    {"text": "INR 250 debited via UPI at DMart on 19-07-2026. HDFC Bank A/c XX4567", "amount": 250, "merchant": "DMart", "bank": "HDFC Bank", "txn_type": "debit", "cat": "others", "date": "2026-07-19T12:00:00"},
    {"text": "INR 1500 debited at Decathlon on 26-07-2026. SBI A/c XX8901", "amount": 1500, "merchant": "Decathlon", "bank": "SBI", "txn_type": "debit", "cat": "others", "date": "2026-07-26T15:30:00"},
    {"text": "INR 5000 credited. UPI transfer from Rahul. SBI A/c XX8901 on 14-07-2026", "amount": 5000, "merchant": None, "bank": "SBI", "txn_type": "credit", "cat": "transfer", "date": "2026-07-14T18:00:00"},
    {"text": "INR 3000 credited. Refund from Flipkart. HDFC Bank A/c XX4567 on 30-07-2026", "amount": 3000, "merchant": "Flipkart", "bank": "HDFC Bank", "txn_type": "credit", "cat": "others", "date": "2026-07-30T10:00:00"},

    # ═══ AUGUST 2026 ═══
    {"text": "INR 60000 credited. Salary from TechCorp. HDFC Bank A/c XX4567 on 01-08-2026", "amount": 60000, "merchant": None, "bank": "HDFC Bank", "txn_type": "credit", "cat": "transfer", "date": "2026-08-01T09:00:00"},
    {"text": "INR 12000 debited. Home Loan EMI. HDFC Bank A/c XX4567 on 05-08-2026", "amount": 12000, "merchant": None, "bank": "HDFC Bank", "txn_type": "debit", "cat": "emi", "date": "2026-08-05T08:30:00"},
    {"text": "INR 3500 debited. Car Loan EMI - Bajaj Finserv. SBI A/c XX8901 on 05-08-2026", "amount": 3500, "merchant": None, "bank": "SBI", "txn_type": "debit", "cat": "emi", "date": "2026-08-05T08:35:00"},
    {"text": "INR 420 debited via UPI at Swiggy on 03-08-2026. HDFC Bank A/c XX4567", "amount": 420, "merchant": "Swiggy", "bank": "HDFC Bank", "txn_type": "debit", "cat": "food", "date": "2026-08-03T20:30:00"},
    {"text": "INR 275 debited at Zomato on 07-08-2026. ICICI Bank A/c XX1234", "amount": 275, "merchant": "Zomato", "bank": "ICICI Bank", "txn_type": "debit", "cat": "food", "date": "2026-08-07T13:00:00"},
    {"text": "INR 159 debited via UPI at Domino's on 14-08-2026. Axis Bank A/c XX5678", "amount": 159, "merchant": "Domino's", "bank": "Axis Bank", "txn_type": "debit", "cat": "food", "date": "2026-08-14T19:30:00"},
    {"text": "INR 380 debited at KFC on 21-08-2026. HDFC Bank A/c XX4567", "amount": 380, "merchant": "KFC", "bank": "HDFC Bank", "txn_type": "debit", "cat": "food", "date": "2026-08-21T12:45:00"},
    {"text": "INR 720 debited at Subway on 28-08-2026. SBI A/c XX8901", "amount": 720, "merchant": "Subway", "bank": "SBI", "txn_type": "debit", "cat": "food", "date": "2026-08-28T18:15:00"},
    {"text": "INR 220 debited via UPI at Uber on 05-08-2026. HDFC Bank A/c XX4567", "amount": 220, "merchant": "Uber", "bank": "HDFC Bank", "txn_type": "debit", "cat": "transport", "date": "2026-08-05T19:00:00"},
    {"text": "INR 310 debited at Ola on 12-08-2026. ICICI Bank A/c XX1234", "amount": 310, "merchant": "Ola", "bank": "ICICI Bank", "txn_type": "debit", "cat": "transport", "date": "2026-08-12T08:30:00"},
    {"text": "INR 89 debited via UPI at Rapido on 19-08-2026. SBI A/c XX8901", "amount": 89, "merchant": "Rapido", "bank": "SBI", "txn_type": "debit", "cat": "transport", "date": "2026-08-19T17:20:00"},
    {"text": "INR 2400 debited at IRCTC on 22-08-2026. HDFC Bank A/c XX4567", "amount": 2400, "merchant": "IRCTC", "bank": "HDFC Bank", "txn_type": "debit", "cat": "transport", "date": "2026-08-22T10:00:00"},
    {"text": "INR 3499 debited at Amazon on 10-08-2026. HDFC Bank A/c XX4567", "amount": 3499, "merchant": "Amazon", "bank": "HDFC Bank", "txn_type": "debit", "cat": "shopping", "date": "2026-08-10T15:30:00"},
    {"text": "INR 899 debited at Myntra on 15-08-2026. Axis Bank A/c XX5678", "amount": 899, "merchant": "Myntra", "bank": "Axis Bank", "txn_type": "debit", "cat": "shopping", "date": "2026-08-15T12:00:00"},
    {"text": "INR 1999 debited at Flipkart on 25-08-2026. ICICI Bank A/c XX1234", "amount": 1999, "merchant": "Flipkart", "bank": "ICICI Bank", "txn_type": "debit", "cat": "shopping", "date": "2026-08-25T11:15:00"},
    {"text": "INR 599 debited. Airtel prepaid recharge. HDFC Bank A/c XX4567 on 01-08-2026", "amount": 599, "merchant": "Airtel", "bank": "HDFC Bank", "txn_type": "debit", "cat": "utilities", "date": "2026-08-01T10:00:00"},
    {"text": "INR 2100 debited. Electricity Bill. SBI A/c XX8901 on 10-08-2026", "amount": 2100, "merchant": None, "bank": "SBI", "txn_type": "debit", "cat": "utilities", "date": "2026-08-10T10:30:00"},
    {"text": "INR 1499 debited. Jio Fiber broadband. ICICI Bank A/c XX1234 on 15-08-2026", "amount": 1499, "merchant": "Jio", "bank": "ICICI Bank", "txn_type": "debit", "cat": "utilities", "date": "2026-08-15T10:00:00"},
    {"text": "INR 299 debited. Netflix subscription. HDFC Bank A/c XX4567 on 20-08-2026", "amount": 299, "merchant": "Netflix", "bank": "HDFC Bank", "txn_type": "debit", "cat": "utilities", "date": "2026-08-20T10:00:00"},
    {"text": "INR 5000 debited at Groww on 01-08-2026. SIP installment. HDFC Bank A/c XX4567", "amount": 5000, "merchant": "Groww", "bank": "HDFC Bank", "txn_type": "debit", "cat": "investment", "date": "2026-08-01T11:00:00"},
    {"text": "INR 3000 debited at Zerodha on 15-08-2026. Axis Bank A/c XX5678", "amount": 3000, "merchant": "Zerodha", "bank": "Axis Bank", "txn_type": "debit", "cat": "investment", "date": "2026-08-15T14:00:00"},
    {"text": "INR 1200 debited at Apollo on 08-08-2026. HDFC Bank A/c XX4567", "amount": 1200, "merchant": "Apollo", "bank": "HDFC Bank", "txn_type": "debit", "cat": "health", "date": "2026-08-08T11:30:00"},
    {"text": "INR 450 debited at Netmeds on 20-08-2026. SBI A/c XX8901", "amount": 450, "merchant": "Netmeds", "bank": "SBI", "txn_type": "debit", "cat": "health", "date": "2026-08-20T16:00:00"},
    {"text": "INR 999 debited at Udemy on 18-08-2026. HDFC Bank A/c XX4567", "amount": 999, "merchant": "Udemy", "bank": "HDFC Bank", "txn_type": "debit", "cat": "education", "date": "2026-08-18T20:00:00"},
    {"text": "INR 3000 credited. UPI transfer from Priya. HDFC Bank A/c XX4567 on 10-08-2026", "amount": 3000, "merchant": None, "bank": "HDFC Bank", "txn_type": "credit", "cat": "transfer", "date": "2026-08-10T19:00:00"},
    {"text": "INR 1500 debited via UPI to Raj. SBI A/c XX8901 on 22-08-2026", "amount": 1500, "merchant": None, "bank": "SBI", "txn_type": "debit", "cat": "transfer", "date": "2026-08-22T20:30:00"},
    {"text": "INR 350 debited via UPI at DMart on 16-08-2026. ICICI Bank A/c XX1234", "amount": 350, "merchant": "DMart", "bank": "ICICI Bank", "txn_type": "debit", "cat": "others", "date": "2026-08-16T13:00:00"},
    {"text": "INR 2200 debited at Croma on 27-08-2026. HDFC Bank A/c XX4567", "amount": 2200, "merchant": "Croma", "bank": "HDFC Bank", "txn_type": "debit", "cat": "others", "date": "2026-08-27T14:30:00"},

    # ═══ SEPTEMBER 2026 ═══
    {"text": "INR 60000 credited. Salary from TechCorp. HDFC Bank A/c XX4567 on 01-09-2026", "amount": 60000, "merchant": None, "bank": "HDFC Bank", "txn_type": "credit", "cat": "transfer", "date": "2026-09-01T09:00:00"},
    {"text": "INR 12000 debited. Home Loan EMI. HDFC Bank A/c XX4567 on 05-09-2026", "amount": 12000, "merchant": None, "bank": "HDFC Bank", "txn_type": "debit", "cat": "emi", "date": "2026-09-05T08:30:00"},
    {"text": "INR 3500 debited. Car Loan EMI - Bajaj Finserv. SBI A/c XX8901 on 05-09-2026", "amount": 3500, "merchant": None, "bank": "SBI", "txn_type": "debit", "cat": "emi", "date": "2026-09-05T08:35:00"},
    {"text": "INR 290 debited via UPI at Swiggy on 04-09-2026. HDFC Bank A/c XX4567", "amount": 290, "merchant": "Swiggy", "bank": "HDFC Bank", "txn_type": "debit", "cat": "food", "date": "2026-09-04T21:00:00"},
    {"text": "INR 410 debited at Zomato on 11-09-2026. ICICI Bank A/c XX1234", "amount": 410, "merchant": "Zomato", "bank": "ICICI Bank", "txn_type": "debit", "cat": "food", "date": "2026-09-11T13:30:00"},
    {"text": "INR 199 debited via UPI at Pizza Hut on 18-09-2026. Axis Bank A/c XX5678", "amount": 199, "merchant": "Pizza Hut", "bank": "Axis Bank", "txn_type": "debit", "cat": "food", "date": "2026-09-18T20:00:00"},
    {"text": "INR 550 debited at Starbucks on 25-09-2026. HDFC Bank A/c XX4567", "amount": 550, "merchant": "Starbucks", "bank": "HDFC Bank", "txn_type": "debit", "cat": "food", "date": "2026-09-25T16:45:00"},
    {"text": "INR 160 debited via UPI at Uber on 08-09-2026. SBI A/c XX8901", "amount": 160, "merchant": "Uber", "bank": "SBI", "txn_type": "debit", "cat": "transport", "date": "2026-09-08T18:30:00"},
    {"text": "INR 280 debited at Ola on 15-09-2026. HDFC Bank A/c XX4567", "amount": 280, "merchant": "Ola", "bank": "HDFC Bank", "txn_type": "debit", "cat": "transport", "date": "2026-09-15T09:45:00"},
    {"text": "INR 2799 debited at Amazon on 10-09-2026. ICICI Bank A/c XX1234", "amount": 2799, "merchant": "Amazon", "bank": "ICICI Bank", "txn_type": "debit", "cat": "shopping", "date": "2026-09-10T14:00:00"},
    {"text": "INR 1599 debited at Flipkart on 20-09-2026. HDFC Bank A/c XX4567", "amount": 1599, "merchant": "Flipkart", "bank": "HDFC Bank", "txn_type": "debit", "cat": "shopping", "date": "2026-09-20T12:30:00"},
    {"text": "INR 599 debited. Airtel prepaid recharge. HDFC Bank A/c XX4567 on 01-09-2026", "amount": 599, "merchant": "Airtel", "bank": "HDFC Bank", "txn_type": "debit", "cat": "utilities", "date": "2026-09-01T10:00:00"},
    {"text": "INR 1650 debited. Electricity Bill. SBI A/c XX8901 on 12-09-2026", "amount": 1650, "merchant": None, "bank": "SBI", "txn_type": "debit", "cat": "utilities", "date": "2026-09-12T10:30:00"},
    {"text": "INR 299 debited. Spotify Premium. HDFC Bank A/c XX4567 on 18-09-2026", "amount": 299, "merchant": "Spotify", "bank": "HDFC Bank", "txn_type": "debit", "cat": "utilities", "date": "2026-09-18T10:00:00"},
    {"text": "INR 950 debited at Apollo on 14-09-2026. HDFC Bank A/c XX4567", "amount": 950, "merchant": "Apollo", "bank": "HDFC Bank", "txn_type": "debit", "cat": "health", "date": "2026-09-14T11:00:00"},
    {"text": "INR 1500 debited at Coursera on 09-09-2026. Axis Bank A/c XX5678", "amount": 1500, "merchant": "Coursera", "bank": "Axis Bank", "txn_type": "debit", "cat": "education", "date": "2026-09-09T19:00:00"},
    {"text": "INR 8000 credited. UPI transfer from Mom. SBI A/c XX8901 on 07-09-2026", "amount": 8000, "merchant": None, "bank": "SBI", "txn_type": "credit", "cat": "transfer", "date": "2026-09-07T17:00:00"},
    {"text": "INR 5000 debited at Groww on 01-09-2026. SIP installment. HDFC Bank A/c XX4567", "amount": 5000, "merchant": "Groww", "bank": "HDFC Bank", "txn_type": "debit", "cat": "investment", "date": "2026-09-01T11:00:00"},
]


def auto_seed():
    """Seed test data if database is empty."""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.phone == PHONE).first()
        if not user:
            user = User(phone=PHONE, name="Satyam", monthly_income=60000, financial_goal="save_more")
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"[SEED] Created user {PHONE}")

        count = db.query(Transaction).filter(Transaction.user_id == user.id).count()
        if count > 0:
            print(f"[SEED] Database already has {count} transactions — skipping.")
            return

        print(f"[SEED] No transactions found — seeding {len(SEED_DATA)} test records...")
        for item in SEED_DATA:
            txn = Transaction(
                user_id=user.id,
                raw_text=item["text"],
                amount=item["amount"],
                merchant=item["merchant"],
                bank=item["bank"],
                transaction_type=item["txn_type"],
                received_at=datetime.fromisoformat(item["date"]),
                predicted_category=item["cat"],
                ml_confidence=0.90,
                all_scores=json.dumps({item["cat"]: 0.90}),
                pattern_category=None,
                final_category=item["cat"],
                is_corrected=False,
            )
            db.add(txn)
        db.commit()
        print(f"[SEED] Done — {len(SEED_DATA)} transactions seeded.")
    except Exception as e:
        print(f"[SEED] Error: {e}")
    finally:
        db.close()
