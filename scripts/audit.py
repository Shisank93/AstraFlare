import os
import sys
import json
import pickle
import numpy as np
import pandas as pd
from collections import Counter
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
from sklearn.dummy import DummyClassifier
from sklearn.model_selection import GroupShuffleSplit, StratifiedGroupKFold
import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ml.dataset_generator import generate_ml_dataset, FEATURE_COLUMNS
from ml.splitter import FacilityGroupSplitter

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ml", "artifacts", "gbdt_model_v1.0.pkl"))

def main():
    print("=== FINAL ML VALIDATION AUDIT ===")
    
    # 1. Load the Model
    with open(MODEL_PATH, "rb") as f:
        model_artifact = pickle.load(f)
        
    base_model = model_artifact["base_model"]
    calibrated_model = model_artifact["calibrated_model"]
    classes = model_artifact["classes"]
    class_to_idx = model_artifact["class_to_idx"]
    idx_to_class = model_artifact["idx_to_class"]
    
    print("\n--- 1. DATASET AUDIT ---")
    raw_res = generate_ml_dataset(limit=8700, allow_non_real=False, label_mode="INDEPENDENT_EXTERNAL")
    dataset = raw_res["dataset"]
    
    # Convert to DataFrame for easy analysis
    df = pd.DataFrame(dataset)
    
    # Filter only labeled
    df_labeled = df[df["label"].isin(classes)].copy()
    df_labeled["label_idx"] = df_labeled["label"].map(class_to_idx)
    
    print(f"Total labeled samples: {len(df_labeled)}")
    print(f"Feature count: {len(FEATURE_COLUMNS)}")
    print(f"Target column: label")
    print(f"Class names: {classes}")
    
    counts = df_labeled["label"].value_counts()
    for cls in classes:
        cnt = counts.get(cls, 0)
        pct = (cnt / len(df_labeled)) * 100
        print(f"  {cls}: {cnt} ({pct:.1f}%)")
        
    print(f"Missing values:\n{df_labeled[FEATURE_COLUMNS].isna().sum().to_dict()}")
    print(f"Duplicate rows (features only): {df_labeled[FEATURE_COLUMNS].duplicated().sum()}")
    print(f"Duplicate event IDs: {df_labeled['physical_event_id'].duplicated().sum()}")
    print(f"Duplicate coordinates/timestamps: {df_labeled[['latitude', 'longitude', 'acq_timestamp']].duplicated().sum()}")
    
    print("\n--- 2. TRAIN/TEST SPLIT AUDIT ---")
    splitter = FacilityGroupSplitter(train_ratio=0.8)
    train_data, test_data = splitter.split(dataset)
    
    df_train = pd.DataFrame([d for d in train_data if d.get("label") in classes])
    df_test = pd.DataFrame([d for d in test_data if d.get("label") in classes])
    
    if not df_train.empty:
        df_train["label_idx"] = df_train["label"].map(class_to_idx)
    if not df_test.empty:
        df_test["label_idx"] = df_test["label"].map(class_to_idx)
    
    train_events = set(df_train["physical_event_id"].unique()) if not df_train.empty else set()
    test_events = set(df_test["physical_event_id"].unique()) if not df_test.empty else set()
    
    overlap = train_events.intersection(test_events)
    
    print("Split method: FacilityGroupSplitter")
    print(f"Train size: {len(df_train)}")
    print(f"Test size: {len(df_test)}")
    print("Random seed: 42 (in model/splitter)")
    print(f"Event overlap between train and test: {len(overlap)} events")
    
    print("\n--- 3. LEAKAGE AUDIT ---")
    if hasattr(base_model, "feature_importances_") or hasattr(base_model, "feature_importances_"):
        # Not available for HistGradientBoostingClassifier easily without permutation
        print("Feature importance not directly exposed by HistGradientBoostingClassifier without permutation.")
    else:
        print("Cannot extract raw feature importances.")
        
    for f in FEATURE_COLUMNS:
        print(f"Checking feature: {f}")
        # Note: We look closely at: historical_count_30d, frp_anomaly_zscore
        if "label" in f or "class" in f or "gt_" in f:
            print(f"  [!] WARNING: Suspicious feature name '{f}'")
    
    print("\n--- 4. METRICS ---")
    X_test = df_test[FEATURE_COLUMNS].values.astype(np.float32)
    y_test = df_test["label_idx"].values.astype(np.int64)
    
    if len(X_test) > 0:
        y_pred = calibrated_model.predict(X_test)
        
        print("Classification Report:")
        print(classification_report(y_test, y_pred, target_names=[idx_to_class[i] for i in range(len(classes))]))
        print("Confusion Matrix:")
        print(confusion_matrix(y_test, y_pred))
    
    print("\n--- 5. BASELINE COMPARISON ---")
    if len(df_train) > 0 and len(df_test) > 0:
        X_train = df_train[FEATURE_COLUMNS].values.astype(np.float32)
        y_train = df_train["label_idx"].values.astype(np.int64)
        
        dummy = DummyClassifier(strategy="most_frequent")
        dummy.fit(X_train, y_train)
        dummy_pred = dummy.predict(X_test)
        print("Majority-Class Baseline Report:")
        print(classification_report(y_test, dummy_pred, labels=[0,1,2], target_names=classes, zero_division=0))
        
    print("\n--- 6. HOLDOUT VALIDATION (GroupShuffleSplit) ---")
    if len(df_labeled) > 0:
        gss = GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=42)
        X_all = df_labeled[FEATURE_COLUMNS].values.astype(np.float32)
        y_all = df_labeled["label_idx"].values.astype(np.int64)
        groups = df_labeled["physical_event_id"].values
        
        for train_idx, test_idx in gss.split(X_all, y_all, groups=groups):
            X_tr, y_tr = X_all[train_idx], y_all[train_idx]
            X_te, y_te = X_all[test_idx], y_all[test_idx]
            
            from sklearn.ensemble import HistGradientBoostingClassifier
            test_model = HistGradientBoostingClassifier(random_state=42)
            test_model.fit(X_tr, y_tr)
            y_pred_gss = test_model.predict(X_te)
            print("GroupShuffleSplit Validation Results:")
            print(classification_report(y_te, y_pred_gss, labels=[0,1,2], target_names=classes, zero_division=0))

    print("\n--- 7. TEMPORAL VALIDATION ---")
    df_labeled["acq_timestamp_dt"] = pd.to_datetime(df_labeled["acq_timestamp"])
    df_sorted = df_labeled.sort_values(by="acq_timestamp_dt")
    
    split_idx = int(len(df_sorted) * 0.8)
    df_temp_train = df_sorted.iloc[:split_idx]
    df_temp_test = df_sorted.iloc[split_idx:]
    
    if len(df_temp_train) > 0 and len(df_temp_test) > 0:
        X_temp_train = df_temp_train[FEATURE_COLUMNS].values.astype(np.float32)
        y_temp_train = df_temp_train["label_idx"].values.astype(np.int64)
        X_temp_test = df_temp_test[FEATURE_COLUMNS].values.astype(np.float32)
        y_temp_test = df_temp_test["label_idx"].values.astype(np.int64)
        
        temp_model = HistGradientBoostingClassifier(random_state=42)
        temp_model.fit(X_temp_train, y_temp_train)
        y_pred_temp = temp_model.predict(X_temp_test)
        
        print("Chronological Temporal Split Validation:")
        print(classification_report(y_temp_test, y_pred_temp, labels=[0,1,2], target_names=classes, zero_division=0))
    
    print("\n--- 8. CONFIDENCE ---")
    if len(X_test) > 0:
        y_prob = calibrated_model.predict_proba(X_test)
        max_probs = np.max(y_prob, axis=1)
        print(f"Mean confidence: {np.mean(max_probs):.4f}")
        print(f"Median confidence: {np.median(max_probs):.4f}")
        print(f"Percentage > 0.90: {np.mean(max_probs > 0.90)*100:.1f}%")
        print(f"Percentage > 0.95: {np.mean(max_probs > 0.95)*100:.1f}%")
        print(f"Percentage < 0.70: {np.mean(max_probs < 0.70)*100:.1f}%")

if __name__ == "__main__":
    main()
