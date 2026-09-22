"""
analyze_real.py
---------------
Runs the saved ML models against a real SMS-Exporter CSV export and reports
filter + category accuracy. Also saves a JSON batch file ready for
backend/load_real_sms.py so the real messages can be pushed into the app.

Expects the SMS-Exporter android CSV format:
    DateTime, Direction, Contact, Phone, Content, Type

Usage:
    python analyze_real.py --csv "data/All Conversations 2026-09-22 125550.csv"
    python analyze_real.py --csv "data/....csv" --models models
"""

import argparse
import csv
import json
import os
import sys

import joblib
from sklearn.metrics import accuracy_score, classification_report

from label_rules import is_financial, label_category

BASE = os.path.dirname(os.path.abspath(__file__))


def parse_sms_export(path: str) -> list[dict]:
    """Return list of {sms_id, text, received_at, sender} for received SMS rows."""
    rows = []
    with open(path, encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = next((r for r in reader if r and r[0].strip() == "DateTime"), None)
        if header is None:
            sys.exit("Header row ('DateTime,...') not found in " + path)
        for i, r in enumerate(reader):
            if len(r) < 6:
                continue
            dt, direction, contact, phone, content, typ = (r[j].strip() for j in range(6))
            if typ.upper() != "SMS":
                continue
            if direction.lower() != "received":
                continue
            if not content:
                continue
            rows.append({
                "sms_id":   f"real-{i}",
                "text":     content,
                "received_at": dt.replace(" ", "T"),
                "sender":   phone or contact,
            })

    # Drop exact (text, date) repeats — the exporter can duplicate rows.
    seen, uniq = set(), []
    for x in rows:
        key = (x["text"], x["received_at"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(x)
    return uniq


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to the SMS-Exporter CSV")
    ap.add_argument("--models", default=os.path.join(BASE, "models"))
    ap.add_argument("--out", default=os.path.join(BASE, "data", "real_sms_batch.json"))
    args = ap.parse_args()

    filter_path   = os.path.join(args.models, "filter_model.pkl")
    category_path = os.path.join(args.models, "category_model.pkl")
    if not (os.path.exists(filter_path) and os.path.exists(category_path)):
        sys.exit(f"Models not found in {args.models}")

    print("Loading models...")
    filter_model   = joblib.load(filter_path)
    category_model = joblib.load(category_path)

    print(f"Parsing {args.csv} ...")
    rows = parse_sms_export(args.csv)
    texts = [r["text"] for r in rows]
    print(f"  Received SMS rows (deduped): {len(rows):,}")

    # ---- Filter model vs rule-based truth ----
    print("\n" + "=" * 60)
    print("FILTER MODEL  (financial vs non-financial)")
    print("=" * 60)
    true_f = [is_financial(t) for t in texts]
    pred_f = filter_model.predict(texts)
    print(f"Rule-labelled financial: {sum(true_f):,}  ({sum(true_f)/len(true_f)*100:.1f}%)")
    print(f"Model-labelled financial: {sum(pred_f):,}")
    print(f"Filter accuracy: {accuracy_score(true_f, pred_f)*100:.2f}%")
    print(classification_report(true_f, pred_f, target_names=["Non-financial", "Financial"]))

    # Show a few misclassified samples for intuition
    print("Sample mismatches (up to 8):")
    shown = 0
    for t, tr, pr in zip(texts, true_f, pred_f):
        if tr != pr:
            print(f"  true={tr} pred={pr} :: {t[:120]}")
            shown += 1
            if shown >= 8:
                break

    # ---- Category model vs rule-based truth (financial only) ----
    fin_idx = [i for i in range(len(texts)) if true_f[i]]
    fin_texts = [texts[i] for i in fin_idx]
    true_c = [label_category(t) for t in fin_texts]
    pred_c = category_model.predict(fin_texts)

    print("\n" + "=" * 60)
    print("CATEGORY MODEL  (on financial messages, vs rule labels)")
    print("=" * 60)
    print(f"Category accuracy: {accuracy_score(true_c, pred_c)*100:.2f}%")
    print(classification_report(true_c, pred_c, zero_division=0))

    print("\nCategory breakdown of rule-labelled financial messages:")
    from collections import Counter
    for cat, n in Counter(true_c).most_common():
        print(f"  {cat:<12} {n:>6}")

    # ---- Save batch file for the loader ----
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    fin_saved = sum(1 for t in texts if is_financial(t))
    print(f"\nSaved {len(rows):,} SMS entries to {args.out}")
    print(f"  -> ~{fin_saved:,} are financial per rules and will be parsed by the backend")


if __name__ == "__main__":
    main()