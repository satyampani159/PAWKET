"""
evaluate.py
-----------
Loads the saved .pkl models and runs a detailed evaluation.
Use this any time you retrain to compare model versions.

Usage:
    python evaluate.py --data path/to/SMS-Data.csv
"""

import argparse
import os
import joblib
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score
from label_rules import is_financial, label_category


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True)
    parser.add_argument("--models", default="models", help="Folder with .pkl files")
    return parser.parse_args()


def main():
    args = parse_args()

    # ---- Load models ----
    filter_path   = os.path.join(args.models, "filter_model.pkl")
    category_path = os.path.join(args.models, "category_model.pkl")

    if not os.path.exists(filter_path) or not os.path.exists(category_path):
        print("ERROR: Models not found. Run train_filter.py and train_category.py first.")
        return

    print("Loading models...")
    filter_pipeline   = joblib.load(filter_path)
    category_pipeline = joblib.load(category_path)

    # ---- Load data ----
    print(f"Loading data from {args.data}...")
    df = pd.read_csv(args.data)
    df = df.dropna(subset=["text"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0].reset_index(drop=True)

    # ---- Filter evaluation ----
    print("\n" + "="*60)
    print("FILTER MODEL")
    print("="*60)
    df["true_filter"] = df["text"].apply(is_financial)
    df["pred_filter"] = filter_pipeline.predict(df["text"])
    print(classification_report(
        df["true_filter"], df["pred_filter"],
        target_names=["Non-financial", "Financial"],
    ))

    # ---- Category evaluation (on financial messages only) ----
    fin_df = df[df["true_filter"] == 1].copy()
    fin_df["true_category"] = fin_df["text"].apply(label_category)
    fin_df["pred_category"] = category_pipeline.predict(fin_df["text"])

    print("="*60)
    print("CATEGORY MODEL  (on financial messages only)")
    print("="*60)
    print(classification_report(
        fin_df["true_category"],
        fin_df["pred_category"],
    ))

    # ---- End-to-end pipeline accuracy ----
    print("="*60)
    print("END-TO-END PIPELINE")
    print("="*60)
    print("Simulating full pipeline: filter → category...")

    results = []
    for text in df["text"]:
        is_fin = filter_pipeline.predict([text])[0]
        if is_fin == 1:
            cat = category_pipeline.predict([text])[0]
            conf = max(category_pipeline.predict_proba([text])[0])
        else:
            cat = "ignored"
            conf = 0.0
        results.append({"text": text, "is_financial": is_fin, "category": cat, "confidence": conf})

    results_df = pd.DataFrame(results)
    fin_count = results_df["is_financial"].sum()
    print(f"  Total messages : {len(results_df):,}")
    print(f"  Financial      : {fin_count:,}  ({fin_count/len(results_df)*100:.1f}%)")
    print(f"  Non-financial  : {len(results_df)-fin_count:,}")
    print()
    print("  Category breakdown of detected financial messages:")
    cat_counts = results_df[results_df["is_financial"]==1]["category"].value_counts()
    for cat, count in cat_counts.items():
        print(f"    {cat:<14} {count:>6,}")

    avg_conf = results_df[results_df["is_financial"]==1]["confidence"].mean()
    print(f"\n  Average category confidence: {avg_conf:.3f}")
    print()


if __name__ == "__main__":
    main()
