"""
load_real_sms.py
----------------
Pushes a real SMS batch (JSON produced by ml_pipeline/analyze_real.py) into the
backend through the authenticated /parse/batch endpoint, so the app shows real
world transactions.

Optionally resets the DB first (--reset) so the app contains only real data.

Usage:
    python load_real_sms.py --batch "../ml_pipeline/data/real_sms_batch.json"
    python load_real_sms.py --batch <file> --api <url> --phone <number> --reset
"""

import argparse
import json
import sys

import requests

DEFAULT_API = "https://p01--pawket--bsydrbrvd8nj.code.run"
DEFAULT_PHONE = "+917377044562"


def request_otp(api, phone):
    r = requests.post(f"{api}/auth/request-otp", json={"phone": phone}, timeout=30)
    r.raise_for_status()
    return r.json()


def verify_otp(api, phone, otp):
    r = requests.post(f"{api}/auth/verify-otp", json={"phone": phone, "otp": otp}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("token"):
        sys.exit(f"verify-otp failed: {data}")
    return data["token"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", required=True, help="JSON batch from analyze_real.py")
    ap.add_argument("--api", default=DEFAULT_API)
    ap.add_argument("--phone", default=DEFAULT_PHONE)
    ap.add_argument("--admin-key", default=None, help="X-Admin-Key for /admin/reset")
    ap.add_argument("--reset", action="store_true", help="Clear DB first (seed=false)")
    args = ap.parse_args()

    entries = json.load(open(args.batch, encoding="utf-8"))
    print(f"Loaded {len(entries):,} SMS entries from {args.batch}")

    if args.reset:
        print("\n[RESET] Clearing database (no seed)...")
        headers = {}
        if args.admin_key:
            headers["X-Admin-Key"] = args.admin_key
        r = requests.post(f"{args.api}/admin/reset?seed=false", headers=headers, timeout=60)
        print("  ", r.status_code, r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text)

    # ---- Authenticate (dev OTP is returned in the response) ----
    print(f"\n[OTP] Requesting for {args.phone} ...")
    resp = request_otp(args.api, args.phone)
    msg = resp.get("message", "")
    print("  ", msg)
    import re
    m = re.search(r"DEV:\s*(\d{6})", msg)
    if not m:
        sys.exit("Could not auto-detect dev OTP in response.")
    otp = m.group(1)

    token = verify_otp(args.api, args.phone, otp)
    headers = {"Authorization": f"Bearer {token}"}
    print(f"  Authenticated. Token: {token[:16]}...")

    # ---- Push in batches of 500 ----
    total = {"parsed": 0, "ignored": 0, "duplicates": 0, "errors": 0}
    for start in range(0, len(entries), 500):
        batch = entries[start:start + 500]
        r = requests.post(f"{args.api}/parse/batch", json=batch, headers=headers, timeout=120)
        if r.status_code != 200:
            print(f"  batch {start//500 + 1}: ERROR {r.status_code} {r.text[:200]}")
            total["errors"] += len(batch)
            continue
        res = r.json()
        for k in total:
            total[k] += res.get(k, 0)
        print(f"  batch {start//500 + 1}: parsed={res.get('parsed')} ignored={res.get('ignored')} "
              f"duplicates={res.get('duplicates')} errors={res.get('errors')}")

    print("\n" + "=" * 50)
    print(f"TOTAL: parsed={total['parsed']} ignored={total['ignored']} "
          f"duplicates={total['duplicates']} errors={total['errors']}")

    # ---- Verify what the app will see ----
    me = requests.get(f"{args.api}/auth/me", headers=headers, timeout=30).json()
    print(f"auth/me transaction_count = {me.get('transaction_count')}")

    try:
        months = requests.get(f"{args.api}/analytics/months", headers=headers, timeout=30).json()
        print(f"Available months: {months}")
    except Exception as e:
        print(f"(could not fetch /analytics/months: {e})")


if __name__ == "__main__":
    main()