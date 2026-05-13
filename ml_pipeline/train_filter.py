"""
train_filter.py
---------------
Trains a binary classifier:
    1  →  financial / bank SMS
    0  →  spam / OTP / promotional / personal

Run this first. It saves:
    models/filter_model.pkl
    models/filter_vectorizer.pkl

Usage:
    python train_filter.py --data path/to/SMS-Data.csv
"""

import argparse
import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.pipeline import Pipeline
import matplotlib
matplotlib.use("Agg")           # headless — no display needed
import matplotlib.pyplot as plt

from label_rules import is_financial


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(description="Train the SMS filter model")
    parser.add_argument(
        "--data",
        required=True,
        help="Path to SMS-Data.csv",
    )
    parser.add_argument(
        "--out",
        default="models",
        help="Output directory for .pkl files (default: models/)",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Fraction of data for testing (default: 0.2)",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Data loading & labeling
# ---------------------------------------------------------------------------

def load_and_label(csv_path: str) -> pd.DataFrame:
    print(f"[1/5] Loading data from: {csv_path}")
    df = pd.read_csv(csv_path)

    # Keep only the 'text' column, drop empty rows
    if "text" not in df.columns:
        raise ValueError("CSV must have a 'text' column.")

    df = df.dropna(subset=["text"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0].reset_index(drop=True)

    print(f"    Total rows after cleaning: {len(df):,}")

    # Apply rule-based labeling
    print("[2/5] Labeling rows with rule-based logic...")
    df["label"] = df["text"].apply(is_financial)

    pos = df["label"].sum()
    neg = len(df) - pos
    print(f"    Financial (1): {pos:,}  |  Non-financial (0): {neg:,}")
    print(f"    Class ratio  : {pos/len(df)*100:.1f}% financial")

    return df


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train(df: pd.DataFrame, test_size: float):
    print("[3/5] Splitting into train / test sets...")
    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"],
        test_size=test_size,
        random_state=42,
        stratify=df["label"],   # keeps class ratio same in both splits
    )
    print(f"    Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    print("[4/5] Training TF-IDF + SGD pipeline...")
    pipeline = Pipeline([
        (
            "tfidf",
            TfidfVectorizer(
                ngram_range=(1, 2),     # unigrams + bigrams
                max_features=30_000,
                sublinear_tf=True,      # log(tf) — helps with frequent words
                strip_accents="unicode",
                min_df=2,               # ignore very rare terms
            ),
        ),
        (
            "clf",
            SGDClassifier(
                loss="log_loss",        # gives probability output
                alpha=1e-4,
                max_iter=100,
                random_state=42,
                class_weight="balanced",  # handles class imbalance
                n_jobs=-1,
            ),
        ),
    ])

    pipeline.fit(X_train, y_train)

    return pipeline, X_test, y_test


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

def evaluate(pipeline, X_test, y_test, out_dir: str):
    print("[5/5] Evaluating on test set...")

    y_pred = pipeline.predict(X_test)

    print("\n" + "="*60)
    print("CLASSIFICATION REPORT")
    print("="*60)
    print(classification_report(
        y_test, y_pred,
        target_names=["Non-financial (0)", "Financial (1)"],
    ))

    # Confusion matrix → saved as PNG
    cm = confusion_matrix(y_test, y_pred)
    disp = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=["Non-financial", "Financial"],
    )
    fig, ax = plt.subplots(figsize=(6, 5))
    disp.plot(ax=ax, cmap="Blues", colorbar=False)
    ax.set_title("Filter Model — Confusion Matrix")
    plt.tight_layout()
    cm_path = os.path.join(out_dir, "filter_confusion_matrix.png")
    plt.savefig(cm_path, dpi=120)
    plt.close()
    print(f"    Confusion matrix saved → {cm_path}")

    # Quick sanity check on real-world examples
    samples = [
        ("INR 500 debited from your account via UPI", 1),
        ("Your OTP is 123456 for login", 0),
        ("Earn up to Rs 18000 per month with Zomato delivery", 0),
        ("Rs.95.15 on Zomato charged via Simpl", 1),
        ("Received Rs.600.00 in your a/c from One97 Communications", 1),
        ("Lucknow ya Kolkata? Watch LIVE with Vi cricket pack", 0),
        ("Your EMI of Rs 3200 has been debited", 1),
        ("Use OTP 459679 to log into Swiggy", 0),
    ]

    print("\nSANITY CHECKS")
    print("-"*60)
    preds = pipeline.predict([s[0] for s in samples])
    probs = pipeline.predict_proba([s[0] for s in samples])
    all_pass = True
    for (text, expected), pred, prob in zip(samples, preds, probs):
        status = "✓" if pred == expected else "✗ FAIL"
        if pred != expected:
            all_pass = False
        print(f"  {status}  [{prob[1]:.2f}]  {text[:60]}")
    print()
    if all_pass:
        print("  All sanity checks passed!")
    else:
        print("  Some checks failed — review label_rules.py")


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save(pipeline, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    model_path = os.path.join(out_dir, "filter_model.pkl")
    joblib.dump(pipeline, model_path)
    print(f"\nModel saved → {model_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    args = parse_args()
    df = load_and_label(args.data)
    pipeline, X_test, y_test = train(df, args.test_size)
    evaluate(pipeline, X_test, y_test, args.out)
    save(pipeline, args.out)
    print("\nDone. Run train_category.py next.\n")
