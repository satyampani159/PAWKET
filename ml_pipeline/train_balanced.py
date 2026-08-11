"""
train_balanced.py
-----------------
Retrains both models with balanced category distribution.

Fixes:
  1. "education" had only 1 sample, "health" 14, "transport" 71
  2. "others" dominated at 57%
  3. Generates synthetic examples for underrepresented categories
  4. Uses SMOTE-style oversampling + undersampling

Usage:
    python train_balanced.py --data data/SMS-Data.csv --out models
"""

import argparse
import os
import random
import joblib
import pandas as pd
import numpy as np
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.combine import SMOTETomek
from imblearn.pipeline import Pipeline as ImbPipeline

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from label_rules import is_financial, label_category


# ---------------------------------------------------------------------------
# Synthetic SMS templates for underrepresented categories
# ---------------------------------------------------------------------------

SYNTHETIC_TEMPLATES = {
    "education": [
        "Rs {amt} debited for tuition fee at {school}",
        "Your payment of Rs {amt} for course fee has been processed",
        "Rs {amt} charged for college fee via UPI",
        "Education fee Rs {amt} paid to {school}",
        "Rs {amt} debited for {platform} subscription",
        "Your Rs {amt} payment for coaching class is successful",
        "Rs {amt} spent on exam fee at {school}",
        "School fee Rs {amt} paid via net banking",
        "Rs {amt} debited for {platform} learning subscription",
        "College admission fee Rs {amt} paid successfully",
        "Rs {amt} charged for online course at {platform}",
        "Tuition fee Rs {amt} paid to {school}",
        "Rs {amt} debited for skillshare subscription",
        "Your Rs {amt} payment for coaching has been received",
        "Rs {amt} spent on university exam fee",
    ],
    "health": [
        "Rs {amt} debited at {pharmacy} pharmacy",
        "Payment of Rs {amt} at {hospital} hospital successful",
        "Rs {amt} charged for medical consultation",
        "Your Rs {amt} payment at {pharmacy} is confirmed",
        "Rs {amt} debited for medicine at {pharmacy}",
        "Health checkup Rs {amt} paid at {hospital}",
        "Rs {amt} charged at diagnostic lab {hospital}",
        "Medical bill Rs {amt} paid via UPI",
        "Rs {amt} debited for pharmacy purchase",
        "Insurance premium Rs {amt} paid successfully",
        "Rs {amt} charged for doctor consultation",
        "Dental checkup Rs {amt} paid at {hospital}",
        "Rs {amt} debited for lab test at {hospital}",
        "Medical expense Rs {amt} paid to {pharmacy}",
        "Rs {amt} charged for healthcare service",
    ],
    "transport": [
        "Uber trip ended. Rs {amt} charged to your card",
        "Ola ride Rs {amt} paid via UPI",
        "Rs {amt} debited for IRCTC booking",
        "Rapido auto ride Rs {amt} paid",
        "Rs {amt} charged for metro recharge",
        "Fastag toll Rs {amt} deducted from wallet",
        "Rs {amt} debited for petrol at HP pump",
        "Train ticket Rs {amt} paid via {app}",
        "Flight booking Rs {amt} debited from account",
        "Auto ride Rs {amt} paid to driver",
        "Rs {amt} charged for bus pass recharge",
        "Cab fare Rs {amt} paid via {app}",
        "Rs {amt} debited for parking at mall",
        "Diesel refill Rs {amt} at IndianOil",
        "Ride to airport Rs {amt} charged via {app}",
    ],
    "shopping": [
        "Amazon order Rs {amt} debited from your account",
        "Flipkart purchase Rs {amt} paid via UPI",
        "Rs {amt} charged for Myntra shopping",
        "Your Rs {amt} payment at {store} is successful",
        "Rs {amt} debited for Nykaa order",
        "Meesho order Rs {amt} paid successfully",
        "Rs {amt} charged for Ajio purchase",
        "Online shopping Rs {amt} debited via {app}",
        "Rs {amt} paid for Zara purchase at mall",
        "Flipkart Big Billion order Rs {amt} debited",
        "Rs {amt} charged for H&M shopping",
        "Amazon Prime day purchase Rs {amt} debited",
        "Rs {amt} paid for Puma sneakers via {app}",
        "Myntra End of Reason sale Rs {amt} charged",
        "Rs {amt} debited for Westside shopping",
    ],
    "transfer": [
        "Sent Rs {amt} to {name} via PhonePe",
        "Rs {amt} transferred to {name} successfully",
        "You paid Rs {amt} to {name} via GPay",
        "Rs {amt} sent to {name} via Paytm UPI",
        "Payment of Rs {amt} to {name} completed",
        "Rs {amt} transferred from your account to {name}",
        "You sent Rs {amt} to {name} via BHIM UPI",
        "Rs {amt} paid to {name} for rent",
        "Split bill Rs {amt} sent to {name}",
        "Rs {amt} settled with {name} via PhonePe",
        "Money sent Rs {amt} to {name} successfully",
        "Rs {amt} transferred to {name} via NEFT",
        "You paid Rs {amt} to {name} via GPay UPI",
        "Rs {amt} sent to {name} for dinner split",
        "Payment Rs {amt} to {name} confirmed via {app}",
    ],
    "investment": [
        "SIP of Rs {amt} processed for {fund} Mutual Fund",
        "Rs {amt} invested in {fund} via Groww",
        "Your Rs {amt} SIP has been debited for {fund}",
        "Rs {amt} credited to your Zerodha account",
        "Mutual fund purchase Rs {amt} for {fund}",
        "Rs {amt} invested in Nifty 50 index fund",
        "Fixed deposit Rs {amt} placed with SBI",
        "Rs {amt} debited for ELSS investment",
        "Stock purchase Rs {amt} via Upstox",
        "PPF deposit Rs {amt} credited successfully",
        "Rs {amt} invested in {fund} SIP",
        "Gold bond purchase Rs {amt} debited",
        "Rs {amt} added to recurring deposit",
        "Mutual fund redemption Rs {amt} credited",
        "NPS contribution Rs {amt} debited from account",
    ],
}

SYNTHETIC_NAMES = [
    "Rahul", "Priya", "Amit", "Sneha", "Vikram", "Pooja", "Arjun", "Neha",
    "Rohit", "Anita", "Karan", "Deepa", "Suresh", "Kavita", "Manoj", "Ritu",
]

SYNTHETIC_SCHOOLS = [
    "Delhi Public School", "St Xavier's", "Ryan International", "DAV School",
    "Kendriya Vidyalaya", "Modern School", "Sacred Heart", "Mount Carmel",
]

SYNTHETIC_PHARMACIES = [
    "Apollo", "Netmeds", "PharmEasy", "1mg", "MedPlus", "Netmeds",
    "MedLife", "HealthPlus", " Wellness", "LifeCare",
]

SYNTHETIC_HOSPITALS = [
    "Apollo Hospital", "Fortis", "Max Healthcare", "Manipal Hospital",
    "Narayana Health", "AIIMS", "Lilavati Hospital", "Global Hospital",
]

SYNTHETIC_PLATFORMS = [
    "Byju's", "Unacademy", "Vedantu", "Coursera", "Udemy",
    "Skillshare", "Simplilearn", "Great Learning", "PhysicsWallah",
]

SYNTHETIC_STORES = [
    "Reliance Digital", "Croma", "Vijay Sales", "Tata Cliq", "Myntra",
]

SYNTHETIC_APPS = ["PhonePe", "GPay", "Paytm", "BHIM", "Amazon Pay"]

SYNTHETIC_FUNDS = [
    "HDFC Mid-Cap", "SBI Bluechip", "Axis Growth", "ICICI Prudential",
    "Nippon India", "Mirae Asset", "Parag Parikh", "Quant Small Cap",
]


def generate_synthetic(category, count):
    """Generate synthetic SMS texts for a given category."""
    templates = SYNTHETIC_TEMPLATES[category]
    texts = []
    for _ in range(count):
        tmpl = random.choice(templates)
        amt = random.choice([99, 149, 199, 249, 299, 349, 399, 499, 599, 799, 999, 1299, 1499, 1999, 2499, 2999, 3499, 4999, 5999, 7999, 9999, 14999])
        text = tmpl.format(
            amt=amt,
            name=random.choice(SYNTHETIC_NAMES),
            school=random.choice(SYNTHETIC_SCHOOLS),
            pharmacy=random.choice(SYNTHETIC_PHARMACIES),
            hospital=random.choice(SYNTHETIC_HOSPITALS),
            platform=random.choice(SYNTHETIC_PLATFORMS),
            store=random.choice(SYNTHETIC_STORES),
            app=random.choice(SYNTHETIC_APPS),
            fund=random.choice(SYNTHETIC_FUNDS),
        )
        texts.append(text)
    return texts


# ---------------------------------------------------------------------------
# Balanced data preparation
# ---------------------------------------------------------------------------

def prepare_balanced_data(df):
    """Balance category distribution with SMOTE + synthetic generation."""

    # Step 1: Label all rows
    print("[1/4] Labeling data...")
    df["label"] = df["text"].apply(is_financial)
    fin_df = df[df["label"] == 1].copy()
    fin_df["category"] = fin_df["text"].apply(label_category)

    dist = fin_df["category"].value_counts()
    print("\n    Original distribution:")
    for cat, count in dist.items():
        bar = "#" * min(40, int(count / dist.max() * 40))
        print(f"    {cat:<12} {count:>6,}  {bar}")

    # Step 2: Set target count per category
    # Target: 800 samples per category (except "others" which we undersample)
    TARGET_PER_CATEGORY = 800
    OTHERS_TARGET = 1500  # still largest but not dominant

    print(f"\n[2/4] Balancing to ~{TARGET_PER_CATEGORY} samples per category...")

    balanced_dfs = []

    for cat in dist.index:
        cat_df = fin_df[fin_df["category"] == cat].copy()
        current_count = len(cat_df)

        if cat == "others":
            # Undersample "others"
            target = OTHERS_TARGET
            if current_count > target:
                cat_df = cat_df.sample(n=target, random_state=42)
            balanced_dfs.append(cat_df)

        elif current_count < TARGET_PER_CATEGORY:
            # Oversample: duplicate existing + generate synthetic
            if current_count > 0:
                # Upsample existing with slight noise (shuffle indices)
                repeat_count = min(current_count * 3, TARGET_PER_CATEGORY - 50)
                upsampled = cat_df.sample(n=repeat_count, replace=True, random_state=42)
                balanced_dfs.append(upsampled)

            # Generate synthetic to fill the gap
            synthetic_needed = TARGET_PER_CATEGORY - len(balanced_dfs[-1]) if balanced_dfs else TARGET_PER_CATEGORY
            if synthetic_needed > 0 and cat in SYNTHETIC_TEMPLATES:
                synth_texts = generate_synthetic(cat, synthetic_needed)
                synth_df = pd.DataFrame({
                    "text": synth_texts,
                    "label": 1,
                    "category": cat,
                })
                balanced_dfs.append(synth_df)
        else:
            # Enough samples — take TARGET_PER_CATEGORY
            cat_df = cat_df.sample(n=TARGET_PER_CATEGORY, random_state=42)
            balanced_dfs.append(cat_df)

    balanced = pd.concat(balanced_dfs, ignore_index=True)
    balanced = balanced.sample(frac=1, random_state=42).reset_index(drop=True)

    final_dist = balanced["category"].value_counts()
    print("\n    Balanced distribution:")
    for cat, count in final_dist.items():
        bar = "#" * min(40, int(count / final_dist.max() * 40))
        print(f"    {cat:<12} {count:>6,}  {bar}")

    print(f"\n    Total financial samples: {len(balanced):,}")

    return balanced


# ---------------------------------------------------------------------------
# Training with SMOTE
# ---------------------------------------------------------------------------

def train_filter(df, test_size):
    """Train the binary filter model."""
    print("\n" + "="*60)
    print("TRAINING FILTER MODEL")
    print("="*60)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["label"],
        test_size=test_size, random_state=42, stratify=df["label"],
    )
    print(f"    Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2), max_features=30_000,
            sublinear_tf=True, strip_accents="unicode", min_df=2,
        )),
        ("clf", SGDClassifier(
            loss="log_loss", alpha=1e-4, max_iter=100,
            random_state=42, class_weight="balanced", n_jobs=-1,
        )),
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    print("\n" + classification_report(y_test, y_pred, target_names=["Non-financial", "Financial"]))

    # Sanity checks
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

    print("SANITY CHECKS")
    print("-"*60)
    preds = pipeline.predict([s[0] for s in samples])
    all_pass = True
    for (text, expected), pred in zip(samples, preds):
        status = "PASS" if pred == expected else "FAIL"
        if pred != expected:
            all_pass = False
        print(f"  {status}  [{pred}]  {text[:60]}")
    print()

    return pipeline, X_test, y_test


def train_category(balanced_df, test_size):
    """Train the multi-category model with balanced data."""
    print("\n" + "="*60)
    print("TRAINING CATEGORY MODEL (BALANCED)")
    print("="*60)

    # Drop categories with < 5 samples
    min_count = 5
    valid_cats = balanced_df["category"].value_counts()
    valid_cats = valid_cats[valid_cats >= min_count].index
    df = balanced_df[balanced_df["category"].isin(valid_cats)].reset_index(drop=True)

    X_train, X_test, y_train, y_test = train_test_split(
        df["text"], df["category"],
        test_size=test_size, random_state=42, stratify=df["category"],
    )
    print(f"    Train: {len(X_train):,}  |  Test: {len(X_test):,}")

    # Use imblearn Pipeline for SMOTE inside the pipeline
    pipeline = ImbPipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2), max_features=40_000,
            sublinear_tf=True, strip_accents="unicode", min_df=2,
        )),
        ("smote", SMOTE(random_state=42, k_neighbors=3)),
        ("clf", SGDClassifier(
            loss="log_loss", alpha=5e-5, max_iter=200,
            random_state=42, class_weight="balanced", n_jobs=-1,
        )),
    ])

    pipeline.fit(X_train, y_train)

    # Cross-validation
    print("    Running 5-fold cross-validation...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, df["text"], df["category"], cv=cv, scoring="f1_macro", n_jobs=-1)
    print(f"    CV F1 (macro): {cv_scores.mean():.3f} +/- {cv_scores.std():.3f}")

    y_pred = pipeline.predict(X_test)
    categories = sorted(y_test.unique())
    report_str = classification_report(y_test, y_pred, target_names=categories)
    print("\n" + report_str)

    # Sanity checks
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
        ("College fee Rs 5000 paid to Delhi Public School", "education"),
        ("Rs 250 debited at Apollo Hospital", "health"),
        ("Ola ride Rs 180 paid via PhonePe", "transport"),
        ("Flipkart order Rs 1299 debited", "shopping"),
    ]

    print("SANITY CHECKS")
    print("-"*60)
    texts = [s[0] for s in samples]
    expected = [s[1] for s in samples]
    preds = pipeline.predict(texts)
    all_pass = True
    for text, exp, pred in zip(texts, expected, preds):
        status = "PASS" if pred == exp else f"FAIL (got: {pred})"
        if pred != exp:
            all_pass = False
        print(f"  {status}  [{pred}]  {text[:60]}")
    print()
    if all_pass:
        print("  All sanity checks passed!")
    else:
        print("  Some checks failed — review label_rules.py")

    return pipeline, X_test, y_test


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_models(filter_pipe, category_pipe, out_dir):
    os.makedirs(out_dir, exist_ok=True)

    filter_path = os.path.join(out_dir, "filter_model.pkl")
    joblib.dump(filter_pipe, filter_path)
    print(f"\nFilter model saved -> {filter_path}")

    category_path = os.path.join(out_dir, "category_model.pkl")
    joblib.dump(category_pipe, category_path)
    print(f"Category model saved -> {category_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Balanced retraining")
    parser.add_argument("--data", required=True, help="Path to SMS-Data.csv")
    parser.add_argument("--out", default="models", help="Output directory")
    parser.add_argument("--test-size", type=float, default=0.2)
    args = parser.parse_args()

    # Load and clean
    print(f"Loading data from: {args.data}")
    df = pd.read_csv(args.data)
    df = df.dropna(subset=["text"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0].reset_index(drop=True)
    print(f"Total rows after cleaning: {len(df):,}")

    # Balance
    balanced = prepare_balanced_data(df)

    # Train filter
    filter_pipe, X_test_f, y_test_f = train_filter(df, args.test_size)

    # Train category
    category_pipe, X_test_c, y_test_c = train_category(balanced, args.test_size)

    # Save
    save_models(filter_pipe, category_pipe, args.out)

    print("\nDone. Copy models/ folder to backend/ml/models/\n")
