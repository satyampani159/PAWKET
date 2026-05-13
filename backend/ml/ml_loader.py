"""
ml/ml_loader.py
---------------
Loads both trained models at startup.
All services import from here — models are loaded once, reused everywhere.
"""

import os
import joblib
from pathlib import Path


class MLModels:
    def __init__(self):
        self.filter_pipeline   = None
        self.category_pipeline = None
        self.loaded            = False

    def load(self, models_dir: str = "ml/models"):
        path = Path(models_dir)

        filter_path   = path / "filter_model.pkl"
        category_path = path / "category_model.pkl"

        if not filter_path.exists():
            raise FileNotFoundError(
                f"Filter model not found at {filter_path}\n"
                "Run ml_pipeline/train_filter.py first, then copy models/ here."
            )
        if not category_path.exists():
            raise FileNotFoundError(
                f"Category model not found at {category_path}\n"
                "Run ml_pipeline/train_category.py first, then copy models/ here."
            )

        print(f"[ML] Loading filter model from   {filter_path}")
        self.filter_pipeline   = joblib.load(filter_path)

        print(f"[ML] Loading category model from {category_path}")
        self.category_pipeline = joblib.load(category_path)

        self.loaded = True
        print("[ML] Both models loaded successfully.")

    def predict_filter(self, text: str) -> tuple[int, float]:
        """
        Returns (label, confidence)
        label: 1 = financial, 0 = not financial
        """
        prob  = self.filter_pipeline.predict_proba([text])[0]
        label = int(prob[1] >= 0.5)
        return label, float(prob[1])

    def predict_category(self, text: str) -> tuple[str, float, dict]:
        """
        Returns (category, confidence, all_scores)
        all_scores: {category: probability}
        """
        classes     = self.category_pipeline.classes_
        probs       = self.category_pipeline.predict_proba([text])[0]
        all_scores  = {c: round(float(p), 4) for c, p in zip(classes, probs)}
        best_idx    = probs.argmax()
        category    = classes[best_idx]
        confidence  = float(probs[best_idx])
        return category, confidence, all_scores


# Single global instance — imported by all services
ml_models = MLModels()
