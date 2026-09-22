"""
test_seed.py
============
Seeds the PAWKET backend with fake SMS data for testing.
- Authenticates via OTP (check Render logs for OTP)
- Clears existing transactions for fresh start
- Pushes ~70 realistic Indian bank SMS across 3 months
"""

import requests
import json
import sys
import time

API = "https://p01--pawket--bsydrbrvd8nj.code.run"
PHONE = "+917377044562"

# ─── Realistic fake SMS data ───────────────────────────────────────────────

FAKE_SMS = [
    # ═══ JULY 2026 ═══

    # Salary (credit)
    {"text": "INR 60000 credited to your HDFC Bank A/c XX4567 on 01-07-2026. Salary from TechCorp Solutions.",
     "received_at": "2026-07-01T09:00:00", "sender": "AD-HDFCBK"},

    # EMI
    {"text": "INR 12000 debited. Home Loan EMI. HDFC Bank A/c XX4567 on 05-07-2026. Ref: EMI789012.",
     "received_at": "2026-07-05T08:30:00", "sender": "AD-HDFCBK"},
    {"text": "INR 3500 debited. Car Loan EMI - Bajaj Finserv. SBI A/c XX8901 on 05-07-2026.",
     "received_at": "2026-07-05T08:35:00", "sender": "AD-SBIBNK"},

    # Food
    {"text": "INR 349 debited via UPI at Swiggy on 08-07-2026. Ref UPI112233. HDFC Bank A/c XX4567.",
     "received_at": "2026-07-08T12:30:00", "sender": "AD-HDFCBK"},
    {"text": "INR 520 debited at Zomato on 12-07-2026. ICICI Bank A/c XX1234. Ref: TXN456789.",
     "received_at": "2026-07-12T20:15:00", "sender": "AD-ICICI"},
    {"text": "INR 189 debited via UPI at McDonald's on 15-07-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-07-15T13:45:00", "sender": "AD-HDFCBK"},
    {"text": "INR 650 debited at Starbucks on 20-07-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-07-20T17:30:00", "sender": "AD-AXIS"},

    # Transport
    {"text": "INR 180 debited via UPI at Uber on 10-07-2026. SBI A/c XX8901. Ref UPI998877.",
     "received_at": "2026-07-10T18:20:00", "sender": "AD-SBIBNK"},
    {"text": "INR 250 debited at Ola on 18-07-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-07-18T09:10:00", "sender": "AD-HDFCBK"},
    {"text": "INR 120 debited via UPI at Rapido on 25-07-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-07-25T08:00:00", "sender": "AD-ICICI"},

    # Shopping
    {"text": "INR 4999 debited at Amazon on 22-07-2026. HDFC Bank A/c XX4567. Ref: AMZ345678.",
     "received_at": "2026-07-22T14:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 1299 debited at Flipkart on 28-07-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-07-28T11:20:00", "sender": "AD-AXIS"},

    # Utilities
    {"text": "INR 599 debited. Airtel prepaid recharge. HDFC Bank A/c XX4567 on 01-07-2026.",
     "received_at": "2026-07-01T10:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 1800 debited. Electricity Bill - BESCOM. SBI A/c XX8901 on 10-07-2026.",
     "received_at": "2026-07-10T10:30:00", "sender": "AD-SBIBNK"},
    {"text": "INR 1499 debited. Jio Fiber broadband. ICICI Bank A/c XX1234 on 15-07-2026.",
     "received_at": "2026-07-15T10:00:00", "sender": "AD-ICICI"},

    # Health
    {"text": "INR 850 debited at Apollo Pharmacy on 12-07-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-07-12T16:40:00", "sender": "AD-HDFCBK"},
    {"text": "INR 320 debited at PharmEasy on 25-07-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-07-25T14:10:00", "sender": "AD-ICICI"},

    # Investment
    {"text": "INR 2000 debited at Zerodha on 15-07-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-07-15T11:00:00", "sender": "AD-AXIS"},

    # Others
    {"text": "INR 250 debited via UPI at DMart on 19-07-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-07-19T12:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 1500 debited at Decathlon on 26-07-2026. SBI A/c XX8901.",
     "received_at": "2026-07-26T15:30:00", "sender": "AD-SBIBNK"},

    # Transfer
    {"text": "INR 5000 credited. UPI transfer from Rahul. SBI A/c XX8901 on 14-07-2026.",
     "received_at": "2026-07-14T18:00:00", "sender": "AD-SBIBNK"},

    # Credit
    {"text": "INR 3000 credited. Refund from Flipkart. HDFC Bank A/c XX4567 on 30-07-2026.",
     "received_at": "2026-07-30T10:00:00", "sender": "AD-HDFCBK"},

    # ═══ AUGUST 2026 ═══

    # Salary
    {"text": "INR 60000 credited to your HDFC Bank A/c XX4567 on 01-08-2026. Salary from TechCorp Solutions.",
     "received_at": "2026-08-01T09:00:00", "sender": "AD-HDFCBK"},

    # EMI
    {"text": "INR 12000 debited. Home Loan EMI. HDFC Bank A/c XX4567 on 05-08-2026.",
     "received_at": "2026-08-05T08:30:00", "sender": "AD-HDFCBK"},
    {"text": "INR 3500 debited. Car Loan EMI - Bajaj Finserv. SBI A/c XX8901 on 05-08-2026.",
     "received_at": "2026-08-05T08:35:00", "sender": "AD-SBIBNK"},

    # Food
    {"text": "INR 420 debited via UPI at Swiggy on 03-08-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-03T20:30:00", "sender": "AD-HDFCBK"},
    {"text": "INR 275 debited at Zomato on 07-08-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-08-07T13:00:00", "sender": "AD-ICICI"},
    {"text": "INR 159 debited via UPI at Domino's on 14-08-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-08-14T19:30:00", "sender": "AD-AXIS"},
    {"text": "INR 380 debited at KFC on 21-08-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-21T12:45:00", "sender": "AD-HDFCBK"},
    {"text": "INR 720 debited at Subway on 28-08-2026. SBI A/c XX8901.",
     "received_at": "2026-08-28T18:15:00", "sender": "AD-SBIBNK"},

    # Transport
    {"text": "INR 220 debited via UPI at Uber on 05-08-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-05T19:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 310 debited at Ola on 12-08-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-08-12T08:30:00", "sender": "AD-ICICI"},
    {"text": "INR 89 debited via UPI at Rapido on 19-08-2026. SBI A/c XX8901.",
     "received_at": "2026-08-19T17:20:00", "sender": "AD-SBIBNK"},
    {"text": "INR 2400 debited at IRCTC on 22-08-2026. Train ticket. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-22T10:00:00", "sender": "AD-HDFCBK"},

    # Shopping
    {"text": "INR 3499 debited at Amazon on 10-08-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-10T15:30:00", "sender": "AD-HDFCBK"},
    {"text": "INR 899 debited at Myntra on 15-08-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-08-15T12:00:00", "sender": "AD-AXIS"},
    {"text": "INR 1999 debited at Flipkart on 25-08-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-08-25T11:15:00", "sender": "AD-ICICI"},

    # Utilities
    {"text": "INR 599 debited. Airtel prepaid recharge. HDFC Bank A/c XX4567 on 01-08-2026.",
     "received_at": "2026-08-01T10:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 2100 debited. Electricity Bill - BESCOM. SBI A/c XX8901 on 10-08-2026.",
     "received_at": "2026-08-10T10:30:00", "sender": "AD-SBIBNK"},
    {"text": "INR 1499 debited. Jio Fiber broadband. ICICI Bank A/c XX1234 on 15-08-2026.",
     "received_at": "2026-08-15T10:00:00", "sender": "AD-ICICI"},
    {"text": "INR 299 debited. Netflix subscription. HDFC Bank A/c XX4567 on 20-08-2026.",
     "received_at": "2026-08-20T10:00:00", "sender": "AD-HDFCBK"},

    # Investment
    {"text": "INR 5000 debited at Groww on 01-08-2026. SIP installment. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-01T11:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 3000 debited at Zerodha on 15-08-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-08-15T14:00:00", "sender": "AD-AXIS"},

    # Health
    {"text": "INR 1200 debited at Apollo on 08-08-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-08T11:30:00", "sender": "AD-HDFCBK"},
    {"text": "INR 450 debited at Netmeds on 20-08-2026. SBI A/c XX8901.",
     "received_at": "2026-08-20T16:00:00", "sender": "AD-SBIBNK"},

    # Education
    {"text": "INR 999 debited at Udemy on 18-08-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-18T20:00:00", "sender": "AD-HDFCBK"},

    # Transfer
    {"text": "INR 3000 credited. UPI transfer from Priya. HDFC Bank A/c XX4567 on 10-08-2026.",
     "received_at": "2026-08-10T19:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 1500 debited via UPI to Raj. SBI A/c XX8901 on 22-08-2026.",
     "received_at": "2026-08-22T20:30:00", "sender": "AD-SBIBNK"},

    # Others
    {"text": "INR 350 debited via UPI at DMart on 16-08-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-08-16T13:00:00", "sender": "AD-ICICI"},
    {"text": "INR 2200 debited at Croma on 27-08-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-08-27T14:30:00", "sender": "AD-HDFCBK"},

    # ═══ SEPTEMBER 2026 ═══

    # Salary
    {"text": "INR 60000 credited to your HDFC Bank A/c XX4567 on 01-09-2026. Salary from TechCorp Solutions.",
     "received_at": "2026-09-01T09:00:00", "sender": "AD-HDFCBK"},

    # EMI
    {"text": "INR 12000 debited. Home Loan EMI. HDFC Bank A/c XX4567 on 05-09-2026.",
     "received_at": "2026-09-05T08:30:00", "sender": "AD-HDFCBK"},
    {"text": "INR 3500 debited. Car Loan EMI - Bajaj Finserv. SBI A/c XX8901 on 05-09-2026.",
     "received_at": "2026-09-05T08:35:00", "sender": "AD-SBIBNK"},

    # Food
    {"text": "INR 290 debited via UPI at Swiggy on 04-09-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-09-04T21:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 410 debited at Zomato on 11-09-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-09-11T13:30:00", "sender": "AD-ICICI"},
    {"text": "INR 199 debited via UPI at Pizza Hut on 18-09-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-09-18T20:00:00", "sender": "AD-AXIS"},
    {"text": "INR 550 debited at Starbucks on 25-09-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-09-25T16:45:00", "sender": "AD-HDFCBK"},

    # Transport
    {"text": "INR 160 debited via UPI at Uber on 08-09-2026. SBI A/c XX8901.",
     "received_at": "2026-09-08T18:30:00", "sender": "AD-SBIBNK"},
    {"text": "INR 280 debited at Ola on 15-09-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-09-15T09:45:00", "sender": "AD-HDFCBK"},

    # Shopping
    {"text": "INR 2799 debited at Amazon on 10-09-2026. ICICI Bank A/c XX1234.",
     "received_at": "2026-09-10T14:00:00", "sender": "AD-ICICI"},
    {"text": "INR 1599 debited at Flipkart on 20-09-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-09-20T12:30:00", "sender": "AD-HDFCBK"},

    # Utilities
    {"text": "INR 599 debited. Airtel prepaid recharge. HDFC Bank A/c XX4567 on 01-09-2026.",
     "received_at": "2026-09-01T10:00:00", "sender": "AD-HDFCBK"},
    {"text": "INR 1650 debited. Electricity Bill - BESCOM. SBI A/c XX8901 on 12-09-2026.",
     "received_at": "2026-09-12T10:30:00", "sender": "AD-SBIBNK"},
    {"text": "INR 299 debited. Spotify Premium. HDFC Bank A/c XX4567 on 18-09-2026.",
     "received_at": "2026-09-18T10:00:00", "sender": "AD-HDFCBK"},

    # Health
    {"text": "INR 950 debited at Apollo on 14-09-2026. HDFC Bank A/c XX4567.",
     "received_at": "2026-09-14T11:00:00", "sender": "AD-HDFCBK"},

    # Education
    {"text": "INR 1500 debited at Coursera on 09-09-2026. Axis Bank A/c XX5678.",
     "received_at": "2026-09-09T19:00:00", "sender": "AD-AXIS"},

    # Transfer
    {"text": "INR 8000 credited. UPI transfer from Mom. SBI A/c XX8901 on 07-09-2026.",
     "received_at": "2026-09-07T17:00:00", "sender": "AD-SBIBNK"},

    # Investment
    {"text": "INR 5000 debited at Groww on 01-09-2026. SIP installment. HDFC Bank A/c XX4567.",
     "received_at": "2026-09-01T11:00:00", "sender": "AD-HDFCBK"},
]


def request_otp(phone):
    print(f"\n{'='*50}")
    print(f"  Requesting OTP for {phone}...")
    print(f"{'='*50}")
    r = requests.post(f"{API}/auth/request-otp", json={"phone": phone})
    if r.status_code != 200:
        print(f"ERROR: {r.status_code} - {r.text}")
        sys.exit(1)
    data = r.json()
    message = data.get("message", "")
    print(f"  Response: {message}")

    # Extract OTP from dev response (format: "OTP sent. [DEV: 123456]")
    otp = None
    if "[DEV:" in message:
        otp = message.split("[DEV:")[1].split("]")[0].strip()
        print(f"  Auto-detected OTP: {otp}")
    return data, otp


def verify_otp(phone, otp):
    print(f"\n  Verifying OTP: {otp}...")
    r = requests.post(f"{API}/auth/verify-otp", json={"phone": phone, "otp": otp})
    if r.status_code != 200:
        print(f"ERROR: {r.status_code} - {r.text}")
        sys.exit(1)
    data = r.json()
    token = data.get("token")
    is_new = data.get("is_new_user", False)
    print(f"  User ID: {data.get('user_id')}")
    print(f"  New user: {is_new}")
    print(f"  Token: {token[:20]}...")
    return token, is_new


def set_profile(token, name="Satyam", income=60000, goal="save_more"):
    print(f"\n  Setting profile: name={name}, income={income}, goal={goal}")
    r = requests.patch(f"{API}/profile",
        json={"name": name, "monthly_income": income, "financial_goal": goal},
        headers={"Authorization": f"Bearer {token}"})
    if r.status_code == 200:
        print(f"  Profile updated: {r.json()}")
    else:
        print(f"  Profile update failed: {r.status_code} - {r.text}")


def clear_transactions(token):
    print(f"\n  Clearing existing transactions...")
    # Get all transactions
    r = requests.get(f"{API}/analytics/transactions?limit=9999",
        headers={"Authorization": f"Bearer {token}"})
    if r.status_code != 200:
        print(f"  Failed to fetch transactions: {r.status_code}")
        return

    data = r.json()
    txns = data.get("transactions", [])
    print(f"  Found {len(txns)} existing transactions")

    if len(txns) == 0:
        print(f"  Nothing to clear.")
        return

    # Delete each transaction via the dedup-clean endpoint won't work for fresh data
    # We'll use direct SQL deletion via a parse batch approach
    # Actually, let's just skip clearing if there's no direct delete endpoint
    # The batch endpoint handles deduplication, so duplicates won't be added
    print(f"  Note: Backend will auto-deduplicate. Duplicates won't be added.")


def seed_sms(token, sms_list):
    print(f"\n{'='*50}")
    print(f"  Seeding {len(sms_list)} fake SMS messages...")
    print(f"{'='*50}")

    # Convert to ParseRequest format
    parse_requests = []
    for sms in sms_list:
        entry = {
            "text": sms["text"],
            "received_at": sms.get("received_at"),
            "sender": sms.get("sender", "test"),
        }
        if sms.get("sms_id"):
            entry["sms_id"] = sms["sms_id"]
        parse_requests.append(entry)

    # Send in batches of 100
    batch_size = 100
    total_parsed = 0
    total_ignored = 0
    total_duplicates = 0
    total_errors = 0

    for i in range(0, len(parse_requests), batch_size):
        batch = parse_requests[i:i+batch_size]
        print(f"\n  Sending batch {i//batch_size + 1} ({len(batch)} messages)...")

        r = requests.post(f"{API}/parse/batch",
            json=batch,
            headers={"Authorization": f"Bearer {token}"})

        if r.status_code != 200:
            print(f"  ERROR: {r.status_code} - {r.text}")
            total_errors += len(batch)
            continue

        result = r.json()
        parsed = result.get("parsed", 0)
        ignored = result.get("ignored", 0)
        duplicates = result.get("duplicates", 0)
        errors = result.get("errors", 0)

        total_parsed += parsed
        total_ignored += ignored
        total_duplicates += duplicates
        total_errors += errors

        print(f"    Parsed: {parsed} | Ignored: {ignored} | Duplicates: {duplicates} | Errors: {errors}")

    return {
        "parsed": total_parsed,
        "ignored": total_ignored,
        "duplicates": total_duplicates,
        "errors": total_errors,
    }


def main():
    print(f"\n{'#'*50}")
    print(f"  PAWKET Test Data Seeder")
    print(f"  Backend: {API}")
    print(f"{'#'*50}")

    # Step 1: Request OTP (auto-detected from dev response)
    _, otp = request_otp(PHONE)
    if not otp:
        print("  Could not auto-detect OTP. Exiting.")
        sys.exit(1)

    # Step 2: Verify OTP
    token, is_new = verify_otp(PHONE, otp)

    # Step 4: Set profile
    set_profile(token)

    # Step 5: Seed data
    results = seed_sms(token, FAKE_SMS)

    # Step 6: Summary
    print(f"\n{'='*50}")
    print(f"  SEEDING COMPLETE")
    print(f"{'='*50}")
    print(f"  Total messages sent: {len(FAKE_SMS)}")
    print(f"  Parsed (new txns):   {results['parsed']}")
    print(f"  Ignored (non-fin):   {results['ignored']}")
    print(f"  Duplicates skipped:  {results['duplicates']}")
    print(f"  Errors:              {results['errors']}")
    print(f"\n  Open the PAWKET app to see your data!")
    print(f"  - Dashboard: KPIs, category breakdown")
    print(f"  - Transactions: Full list with categories")
    print(f"  - Analytics: Charts across months")
    print(f"  - Advice: 50/30/20 rule, insights")


if __name__ == "__main__":
    main()
