"""
train_category.py
-----------------
Trains a multi-class classifier for spending categories:
    food | transport | shopping | health | emi |
    investment | transfer | utilities | education | others

Only runs on rows that the filter model would mark as financial (label=1).
This keeps the category model focused — it never sees spam/OTP messages.

Saves:
    models/category_model.pkl
    models/category_report.txt

Usage:
    python train_category.py --data path/to/SMS-Data.csv
"""

import argparse
import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.pipeline import Pipeline
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from label_rules import is_financial, label_category


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Train the SMS category model")
    parser.add_argument("--data", required=True, help="Path to SMS-Data.csv")
    parser.add_argument("--out", default="models", help="Output directory (default: models/)")
    parser.add_argument("--test-size", type=float, default=0.2)
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Data loading & labeling
# ---------------------------------------------------------------------------

def load_and_label(csv_path: str) -> pd.DataFrame:
    print(f"[1/5] Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)

    if "text" not in df.columns:
        raise ValueError("CSV must have a 'text' column.")

    df = df.dropna(subset=["text"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0].reset_index(drop=True)
    print(f"    Total rows after cleaning: {len(df):,}")

    # Step 1: keep only financial messages
    print("[2/5] Filtering to financial messages only...")
    df["is_financial"] = df["text"].apply(is_financial)
    df = df[df["is_financial"] == 1].copy().reset_index(drop=True)
    print(f"    Financial rows kept: {len(df):,}")

    # Step 2: assign category
    print("    Labeling categories...")
    df["category"] = df["text"].apply(label_category)

    # Show distribution
    dist = df["category"].value_counts()
    print("\n    Category distribution:")
    for cat, count in dist.items():
        bar = "█" * min(40, int(count / dist.max() * 40))
        print(f"    {cat:<12} {count:>6,}  {bar}")

    # Warn if any category is very underrepresented
    min_samples_needed = 20
    low = dist[dist < min_samples_needed]
    if not low.empty:
        print(f"\n    ⚠  Low-sample categories (< {min_samples_needed}): {list(low.index)}")
        print("       Consider adding more keyword patterns in label_rules.py")

    print()
    return df


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(df: pd.DataFrame, test_size: float):
    print("[3/5] Splitting into train / test sets...")

    # Drop categories with too few samples to stratify
    min_count = 5
    valid_cats = df["category"].value_counts()
    valid_cats = valid_cats[valid_cats >= min_count].index
    dropped = df[~df["category"].isin(valid_cats)]["category"].unique()
    if len(dropped):
        print(f"    Dropping very rare categories (< {min_count} samples): {dropped}")
    df = df[df["category"].isin(valid_cats)].reset_index(drop=True)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["category"],
        test_size=test_size,
        random_state=42,
        stratify=df["category"],
    )
    print(f"    Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    print("[4/5] Training TF-IDF + SGD pipeline...")
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),
                max_features=40_000,
                sublinear_tf=True,
                strip_accents="unicode",
                min_df=2,
            ),
        ),
        (
            "clf",
            SGDClassifier(
                loss="log_loss",
                alpha=5e-5,
                max_iter=200,
                random_state=42,
                class_weight="balanced",
                n_jobs=-1,
            ),
        ),
    ])

    pipeline.fit(X_train, y_train)

    # 5-fold cross-validation on training data
    print("    Running 5-fold cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, df["text"], df["category"], cv=cv, scoring="f1_macro", n_jobs=-1)
    print(f"    CV F1 (macro): {cv_scores.mean():.3f} ± {cv_scores.std():.3f}")

    return pipeline, X_test, y_test, df


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(pipeline, X_test, y_test, out_dir: str):
    print("[5/5] Evaluating on test set...")

    y_pred = pipeline.predict(X_test)
    categories = sorted(y_test.unique())

    report_str = classification_report(y_test, y_pred, target_names=categories)
    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    print(report_str)

    # Save report to file
    report_path = os.path.join(out_dir, "category_report.txt")
    with open(report_path, "w") as f:
        f.write(report_str)
    print(f"    Report saved → {report_path}")

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=categories)
    fig, ax = plt.subplots(figsize=(10, 8))
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=categories)
    disp.plot(ax=ax, cmap="Blues", colorbar=True, xticks_rotation=45)
    ax.set_title("Category Model — Confusion Matrix")
    plt.tight_layout()
    cm_path = os.path.join(out_dir, "category_confusion_matrix.png")
    plt.savefig(cm_path, dpi=120)
    plt.close()
    print(f"    Confusion matrix saved → {cm_path}")

    # Sanity checks per category
    samples = [
        ("INR 250 debited via UPI at Swiggy", "food"),
        ("Rs 95 on Zomato charged via Simpl", "food"),
        ("Uber trip ended. Rs 180 charged to your card", "transport"),
        ("IRCTC booking confirmed. Rs 1200 debited", "transport"),
        ("Amazon order placed. Rs 599 debited", "shopping"),
        ("Apollo Pharmacy Rs 340 paid via UPI", "health"),
        ("Your EMI of Rs 3200 has been debited from your account", "emi"),
        ("SIP of Rs 2000 processed for HDFC Mutual Fund", "investment"),
        ("Sent Rs 500 to Rahul via PhonePe", "transfer"),
        ("Jio postpaid bill Rs 399 paid", "utilities"),
        ("Unacademy subscription Rs 1000 debited", "education"),
    ]

    print("\nSANITY CHECKS")
    print("-"*60)
    texts = [s[0] for s in samples]
    expected = [s[1] for s in samples]
    preds = pipeline.predict(texts)
    probs = pipeline.predict_proba(texts)
    classes = pipeline.classes_

    all_pass = True
    for text, exp, pred, prob_row in zip(texts, expected, preds, probs):
        conf = prob_row[list(classes).index(pred)]
        status = "✓" if pred == exp else f"✗ FAIL (got: {pred})"
        if pred != exp:
            all_pass = False
        print(f"  {status}  [{conf:.2f}]  {text[:60]}")

    print()
    if all_pass:
        print("  All sanity checks passed!")
    else:
        print("  Some checks failed — review label_rules.py keyword patterns")


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save(pipeline, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    model_path = os.path.join(out_dir, "category_model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"\nModel saved → {model_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()
    df = load_and_label(args.data)
    pipeline, X_test, y_test, df_filtered = train(df, args.test_size)
    evaluate(pipeline, X_test, y_test, args.out)
    save(pipeline, args.out)
    print("\nDone. Both models trained. Move models/ folder to backend/ml/\n")
