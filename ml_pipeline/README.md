# ml_pipeline

Train the two ML models that power the finance app.

## Folder structure

```
ml_pipeline/
├── data/
│   └── SMS-Data.csv          ← put your dataset here
├── models/                   ← created automatically after training
│   ├── filter_model.pkl
│   ├── category_model.pkl
│   ├── filter_confusion_matrix.png
│   ├── category_confusion_matrix.png
│   └── category_report.txt
├── label_rules.py            ← ALL keyword logic lives here
├── train_filter.py           ← step 1
├── train_category.py         ← step 2
├── evaluate.py               ← run any time to check model quality
└── requirements.txt
```

## Setup

```bash
cd ml_pipeline
pip install -r requirements.txt
```

## Run in order

### Step 1 — Train the filter model (bank vs non-bank)
```bash
python train_filter.py --data data/SMS-Data.csv
```

### Step 2 — Train the category model (food, emi, travel…)
```bash
python train_category.py --data data/SMS-Data.csv
```

### Step 3 — Evaluate both models end-to-end
```bash
python evaluate.py --data data/SMS-Data.csv
```

## What good output looks like

Filter model — you want:
- Precision ≥ 0.90 on class "Financial"
- Recall    ≥ 0.85 on class "Financial"

Category model — you want:
- Macro F1  ≥ 0.75
- No category below 0.60 F1 (if one is low, add more keywords in label_rules.py)

## Improving accuracy

All keyword rules are in `label_rules.py`.

To add a new keyword to a category:
1. Open `label_rules.py`
2. Find the tuple for that category in `CATEGORY_RULES`
3. Add a regex pattern to its list
4. Re-run training — takes ~30 seconds

## After training

Copy the `models/` folder to the backend:
```bash
cp -r models/ ../backend/ml/models/
```
The backend will load both .pkl files at startup.
