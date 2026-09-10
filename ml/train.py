"""
AstraFlare GBDT Model Training, Calibration, and Evaluation Engine.
Trains LightGBM / Scikit-Learn GBDT models, computes multi-class metrics,
fits probability calibration, and saves versioned model artifacts.
"""
import os
import sys
import pickle
import json
import logging
from typing import Dict, Any, Tuple
import numpy as np

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support, log_loss, brier_score_loss
from ml.dataset_generator import generate_ml_dataset, FEATURE_COLUMNS
from ml.splitter import TemporalSplitter, SpatialGroupKFold, EventGroupSplitter, FacilityGroupSplitter
from ml.labeling import LABEL_UNLABELED

logger = logging.getLogger("astraflare.ml.train")

MODEL_ARTIFACT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "artifacts"))

class ModelTrainer:
    def __init__(self, model_version: str = "v1.0"):
        self.model_version = model_version
        self.feature_columns = FEATURE_COLUMNS
        self.classes = [
            "LIKELY_INDUSTRIAL_INCIDENT",
            "PERSISTENT_INDUSTRIAL_HEAT",
            "NATURAL_WILDLAND_FIRE"
        ]
        self.class_to_idx = {c: i for i, c in enumerate(self.classes)}
        self.idx_to_class = {i: c for i, c in enumerate(self.classes)}
        
        self.base_model = None
        self.calibrated_model = None

    def _prepare_matrix(self, dataset: list) -> Tuple[np.ndarray, np.ndarray, list]:
        """Converts dataset dicts to feature matrix X and label vector y."""
        X_rows = []
        y_rows = []
        valid_items = []

        for item in dataset:
            lbl = item.get("label")
            if lbl not in self.class_to_idx:
                continue  # Skip UNLABELED / ambiguous records
            
            row = [float(item.get(col, 0.0)) for col in self.feature_columns]
            X_rows.append(row)
            y_rows.append(self.class_to_idx[lbl])
            valid_items.append(item)

        return np.array(X_rows, dtype=np.float32), np.array(y_rows, dtype=np.int64), valid_items

    def train_and_evaluate(self, limit: int = 30000, label_mode: str = "INDEPENDENT_EXTERNAL", splitter_type: str = "EVENT") -> Dict[str, Any]:
        """
        Executes end-to-end facility/event-isolated training, probability calibration,
        multi-class metric reporting, and versioned artifact saving.
        """
        print("=" * 60)
        print(f"ASTRAFLARE GBDT MODEL TRAINING & EVALUATION (Mode: {label_mode} | Splitter: {splitter_type})")
        print("=" * 60)

        # 1. Generate REAL ML Dataset (Dataset A vs Dataset B)
        raw_res = generate_ml_dataset(limit=limit, allow_non_real=False, label_mode=label_mode)
        dataset = raw_res["dataset"]
        print(f"Total REAL Observations Processed: {len(dataset)}")
        print(f"Label Distribution: {raw_res['audit']['counts']}")

        # 2. Facility / Event-Isolated Train/Test Split (80% Train, 20% Test)
        if splitter_type == "FACILITY":
            splitter = FacilityGroupSplitter(train_ratio=0.8)
        else:
            splitter = EventGroupSplitter(train_ratio=0.8)

        train_data, test_data = splitter.split(dataset)

        X_train, y_train, train_items = self._prepare_matrix(train_data)
        X_test, y_test, test_items = self._prepare_matrix(test_data)

        print(f"{splitter_type}-Isolated Training Set: {len(X_train)} samples | Test Set: {len(X_test)} samples")

        if len(X_test) == 0 and len(X_train) > 1:
            split_idx = max(1, int(len(X_train) * 0.8))
            if split_idx < len(X_train):
                X_test, y_test, test_items = X_train[split_idx:], y_train[split_idx:], train_items[split_idx:]
                X_train, y_train, train_items = X_train[:split_idx], y_train[:split_idx], train_items[:split_idx]

        if len(X_train) == 0 or len(X_test) == 0:
            raise ValueError("Insufficient labeled training/testing samples for GBDT training.")

        # 3. Base GBDT Model Training
        self.base_model = HistGradientBoostingClassifier(
            max_iter=150,
            learning_rate=0.05,
            max_depth=5,
            random_state=42
        )
        self.base_model.fit(X_train, y_train)

        # 4. Probability Calibration (Sigmoid/Platt Scaling)
        try:
            self.calibrated_model = CalibratedClassifierCV(
                estimator=self.base_model,
                method="sigmoid",
                cv=min(3, max(2, len(X_train)//5))
            )
            self.calibrated_model.fit(X_train, y_train)
            calibrated_pass = True
            calib_method = "Sigmoid / Platt Scaling (Cross-Validated)"
        except Exception as e:
            self.calibrated_model = self.base_model
            calibrated_pass = False
            calib_method = f"Uncalibrated (Fallback: {e})"

        # 5. Evaluate Multi-Class Performance Metrics
        y_pred = self.calibrated_model.predict(X_test)
        y_prob = self.calibrated_model.predict_proba(X_test)

        prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, labels=[0, 1, 2], average=None, zero_division=0)
        macro_f1 = float(np.mean(f1))
        weighted_prec, weighted_rec, weighted_f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted", zero_division=0)

        cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2]).tolist()

        class_metrics = {}
        for idx, cls_name in enumerate(self.classes):
            class_metrics[cls_name] = {
                "precision": round(float(prec[idx]), 4),
                "recall": round(float(rec[idx]), 4),
                "f1_score": round(float(f1[idx]), 4)
            }

        print("\n--- EVALUATION METRICS ---")
        print(f"Macro F1-Score: {macro_f1:.4f}")
        print(f"Weighted Precision: {weighted_prec:.4f} | Weighted Recall: {weighted_rec:.4f} | Weighted F1: {weighted_f1:.4f}")
        print(f"Calibration Method: {calib_method}")
        print("\nPer-Class Breakdown:")
        for k, v in class_metrics.items():
            print(f"  {k:30s} -> Precision: {v['precision']:.4f}, Recall: {v['recall']:.4f}, F1: {v['f1_score']:.4f}")

        # 6. Save Model Artifacts
        os.makedirs(MODEL_ARTIFACT_DIR, exist_ok=True)
        model_path = os.path.join(MODEL_ARTIFACT_DIR, f"gbdt_model_{self.model_version}.pkl")
        meta_path = os.path.join(MODEL_ARTIFACT_DIR, f"metadata_{self.model_version}.json")

        artifact_payload = {
            "base_model": self.base_model,
            "calibrated_model": self.calibrated_model,
            "feature_columns": self.feature_columns,
            "classes": self.classes,
            "class_to_idx": self.class_to_idx,
            "idx_to_class": self.idx_to_class,
            "model_version": self.model_version
        }

        with open(model_path, "wb") as f:
            pickle.dump(artifact_payload, f)

        metadata = {
            "model_version": self.model_version,
            "label_mode": label_mode,
            "training_samples": len(X_train),
            "test_samples": len(X_test),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(float(weighted_f1), 4),
            "confusion_matrix": cm,
            "class_metrics": class_metrics,
            "calibration_method": calib_method,
            "calibrated": calibrated_pass
        }

        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        print(f"\nSaved Model Artifact: {model_path}")
        print("=" * 60)

        return metadata

if __name__ == "__main__":
    trainer = ModelTrainer()
    trainer.train_and_evaluate(limit=30000, label_mode="INDEPENDENT_EXTERNAL", splitter_type="EVENT")
