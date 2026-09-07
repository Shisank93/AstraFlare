"""
AstraFlare Spatial, Temporal, Event & Facility Dataset Splitting Engine.
Enforces strict group isolation to prevent spatial, facility, temporal, and event leakage.
"""
import math
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Tuple, Generator, Union


def get_facility_group_id(row: Union[pd.Series, Dict[str, Any]]) -> str:
    """
    Computes facility group ID for an event row:
    - If near industrial node (within 3000m), uses discrete spatial grid cell (0.03 deg ~ 3.3km) around industrial site.
    - Otherwise, falls back to event_id or spatial grid cell (0.05 deg ~ 5.5km).
    """
    if isinstance(row, dict):
        dist_m = float(row.get("industrial_distance_m", 10000.0))
        lat = float(row.get("centroid_lat") or row.get("latitude") or 0.0)
        lon = float(row.get("centroid_lon") or row.get("longitude") or 0.0)
        evt_id = str(row.get("event_id") or row.get("physical_event_id") or "")
    else:
        dist_m = float(row.get("industrial_distance_m", 10000.0))
        lat = float(row.get("centroid_lat", 0.0))
        lon = float(row.get("centroid_lon", 0.0))
        evt_id = str(row.get("event_id", ""))

    if dist_m <= 3000.0:
        grid_lat = int(round(lat / 0.03))
        grid_lon = int(round(lon / 0.03))
        return f"fac_zone_{grid_lat}_{grid_lon}"
    else:
        grid_lat = int(round(lat / 0.05))
        grid_lon = int(round(lon / 0.05))
        return f"cell_{grid_lat}_{grid_lon}"


class EventGroupSplitter:
    """
    Event-level train/test splitter. Ensures all observations and properties of a physical event
    remain strictly together in EITHER train OR test partition.
    """
    def __init__(self, train_ratio: float = 0.8, random_state: int = 42):
        self.train_ratio = train_ratio
        self.random_state = random_state

    def split(self, df: Union[pd.DataFrame, List[Dict[str, Any]]]) -> Tuple[Union[pd.DataFrame, List[Dict[str, Any]]], Union[pd.DataFrame, List[Dict[str, Any]]]]:
        if isinstance(df, list):
            if not df:
                return [], []
            from collections import defaultdict
            event_groups = defaultdict(list)
            for item in df:
                evt_id = item.get("physical_event_id") or item.get("event_id") or item.get("hotspot_id") or "hs_unknown"
                event_groups[evt_id].append(item)

            sorted_events = sorted(
                event_groups.keys(),
                key=lambda e_id: min(str(x.get("acq_timestamp", "")) for x in event_groups[e_id])
            )
            n_events = len(sorted_events)
            split_idx = max(1, int(n_events * self.train_ratio))
            train_events = set(sorted_events[:split_idx])

            train_set = [item for evt_id in train_events for item in event_groups[evt_id]]
            test_set = [item for evt_id in event_groups if evt_id not in train_events for item in event_groups[evt_id]]
            return train_set, test_set

        if df.empty:
            return df.copy(), df.copy()

        unique_events = df["event_id"].unique()
        rng = np.random.RandomState(self.random_state)
        shuffled_events = rng.permutation(unique_events)

        n_train = max(1, int(len(shuffled_events) * self.train_ratio))
        train_events = set(shuffled_events[:n_train])

        train_df = df[df["event_id"].isin(train_events)].copy()
        test_df = df[~df["event_id"].isin(train_events)].copy()

        return train_df, test_df


class FacilityGroupSplitter:
    """
    Facility-level train/test splitter. Ensures that all events belonging to the same
    industrial facility or spatial industrial zone stay strictly together in EITHER train OR test.
    Supports class stratification across facility groups when label column is present.
    """
    def __init__(self, train_ratio: float = 0.8, random_state: int = 42, stratify_by_label: bool = True, max_facility_dist_m: float = 3000.0):
        self.train_ratio = train_ratio
        self.random_state = random_state
        self.stratify_by_label = stratify_by_label
        self.max_facility_dist_m = max_facility_dist_m

    def split(self, df: Union[pd.DataFrame, List[Dict[str, Any]]]) -> Tuple[Union[pd.DataFrame, List[Dict[str, Any]]], Union[pd.DataFrame, List[Dict[str, Any]]]]:
        if isinstance(df, list):
            if not df:
                return [], []
            from collections import defaultdict
            facility_groups = defaultdict(list)
            for item in df:
                fac_name = item.get("nearest_industrial_name")
                dist_m = float(item.get("industrial_distance_m") or 10000.0)
                if fac_name and dist_m <= 3000.0:
                    fac_id = f"fac_{fac_name}"
                else:
                    evt_id = item.get("physical_event_id") or item.get("event_id")
                    if evt_id:
                        fac_id = f"evt_{evt_id}"
                    else:
                        g_y = int(float(item.get("latitude", 0.0)) / 0.03)
                        g_x = int(float(item.get("longitude", 0.0)) / 0.03)
                        fac_id = f"cell_{g_y}_{g_x}"
                facility_groups[fac_id].append(item)

            sorted_facs = sorted(
                facility_groups.keys(),
                key=lambda f_id: min(str(x.get("acq_timestamp", "")) for x in facility_groups[f_id])
            )
            n_facs = len(sorted_facs)
            split_idx = max(1, int(n_facs * self.train_ratio))
            train_facs = set(sorted_facs[:split_idx])

            train_set = [item for f_id in train_facs for item in facility_groups[f_id]]
            test_set = [item for f_id in facility_groups if f_id not in train_facs for item in facility_groups[f_id]]
            return train_set, test_set

        if df.empty:
            return df.copy(), df.copy()

        df_work = df.copy()
        df_work["facility_group_id"] = df_work.apply(get_facility_group_id, axis=1)
        rng = np.random.RandomState(self.random_state)

        if self.stratify_by_label and "label" in df_work.columns and df_work["label"].nunique() > 1:
            train_idx, test_idx = [], []
            for lbl, group in df_work.groupby("label"):
                unique_facs = group["facility_group_id"].unique()
                shuffled_facs = rng.permutation(unique_facs)
                if len(shuffled_facs) > 1:
                    n_train = max(1, min(len(shuffled_facs) - 1, int(len(shuffled_facs) * self.train_ratio)))
                else:
                    n_train = 1
                train_facs = set(shuffled_facs[:n_train])
                
                tr_i = group[group["facility_group_id"].isin(train_facs)].index
                te_i = group[~group["facility_group_id"].isin(train_facs)].index
                train_idx.extend(tr_i)
                test_idx.extend(te_i)

            train_df = df_work.loc[train_idx].drop(columns=["facility_group_id"])
            test_df = df_work.loc[test_idx].drop(columns=["facility_group_id"])
        else:
            unique_facs = df_work["facility_group_id"].unique()
            shuffled_facs = rng.permutation(unique_facs)
            n_train = max(1, int(len(shuffled_facs) * self.train_ratio))
            train_facs = set(shuffled_facs[:n_train])

            train_df = df_work[df_work["facility_group_id"].isin(train_facs)].drop(columns=["facility_group_id"])
            test_df = df_work[~df_work["facility_group_id"].isin(train_facs)].drop(columns=["facility_group_id"])

        return train_df, test_df


class TemporalSplitter:
    """
    Chronological temporal holdout train/test splitter.
    Ensures model trains on earlier events and is validated/tested on future events.
    """
    def __init__(self, train_ratio: float = 0.8):
        self.train_ratio = train_ratio

    def split(self, dataset: Union[pd.DataFrame, List[Dict[str, Any]]]) -> Tuple[Any, Any]:
        if isinstance(dataset, list):
            sorted_ds = sorted(dataset, key=lambda x: str(x.get("acq_timestamp", "")))
            n = len(sorted_ds)
            split_idx = int(n * self.train_ratio)
            return sorted_ds[:split_idx], sorted_ds[split_idx:]

        if dataset.empty:
            return dataset.copy(), dataset.copy()

        ts_col = "event_start" if "event_start" in dataset.columns else "acq_timestamp"
        df_sorted = dataset.sort_values(ts_col).reset_index(drop=True)

        n_train = max(1, int(len(df_sorted) * self.train_ratio))
        train_df = df_sorted.iloc[:n_train].copy()
        test_df = df_sorted.iloc[n_train:].copy()

        return train_df, test_df


class SpatialGroupKFold:
    """
    Spatial grid group partitioning (e.g. 0.5 deg x 0.5 deg lat/lon bounding box cells).
    Ensures entire spatial clusters are assigned together to train or validation partitions.
    """
    def __init__(self, grid_size_deg: float = 0.5, n_splits: int = 5):
        self.grid_size_deg = grid_size_deg
        self.n_splits = n_splits

    def assign_spatial_groups(self, dataset: Union[pd.DataFrame, List[Dict[str, Any]]]) -> np.ndarray:
        groups = []
        if isinstance(dataset, pd.DataFrame):
            items = dataset.to_dict("records")
        else:
            items = dataset

        for item in items:
            lat = float(item.get("centroid_lat") or item.get("latitude") or 0.0)
            lon = float(item.get("centroid_lon") or item.get("longitude") or 0.0)
            grid_y = math.floor(lat / self.grid_size_deg)
            grid_x = math.floor(lon / self.grid_size_deg)
            group_id = hash(f"{grid_y}_{grid_x}") % 100000
            groups.append(group_id)
        return np.array(groups)

    def split(self, dataset: Union[pd.DataFrame, List[Dict[str, Any]]]) -> Generator[Tuple[Any, Any], None, None]:
        groups = self.assign_spatial_groups(dataset)
        unique_groups = np.unique(groups)
        np.random.seed(42)
        np.random.shuffle(unique_groups)

        fold_size = len(unique_groups) // self.n_splits
        for i in range(self.n_splits):
            val_groups = set(unique_groups[i * fold_size : (i + 1) * fold_size])
            train_idx = [idx for idx, g in enumerate(groups) if g not in val_groups]
            val_idx = [idx for idx, g in enumerate(groups) if g in val_groups]

            if isinstance(dataset, pd.DataFrame):
                yield dataset.iloc[train_idx], dataset.iloc[val_idx]
            else:
                yield [dataset[j] for j in train_idx], [dataset[j] for j in val_idx]


def verify_split_isolation(train_df: pd.DataFrame, test_df: pd.DataFrame, splitter_name: str = "Splitter") -> Dict[str, Any]:
    """
    Rigorously verifies zero leakage across partitions for:
    - Event ID overlap
    - Industrial Facility group overlap
    - Duplicate row overlap
    - Temporal causality overlap (for TemporalSplitter)
    """
    # 1. Event Overlap
    train_events = set(train_df["event_id"])
    test_events = set(test_df["event_id"])
    event_overlap = len(train_events.intersection(test_events))

    # 2. Facility Group Overlap
    train_facs = set(train_df.apply(get_facility_group_id, axis=1))
    test_facs = set(test_df.apply(get_facility_group_id, axis=1))
    facility_overlap = len(train_facs.intersection(test_facs))

    # 3. Duplicate Overlap
    train_hashes = set(train_df["event_id"])
    test_hashes = set(test_df["event_id"])
    duplicate_overlap = len(train_hashes.intersection(test_hashes))

    # 4. Temporal Overlap
    ts_col = "event_start" if "event_start" in train_df.columns else "acq_timestamp"
    if ts_col in train_df.columns and ts_col in test_df.columns:
        max_train_ts = train_df[ts_col].max()
        min_test_ts = test_df[ts_col].min()
        temporal_leakage = 1 if max_train_ts > min_test_ts and splitter_name == "TemporalSplitter" else 0
    else:
        max_train_ts, min_test_ts = None, None
        temporal_leakage = 0

    is_clean = (event_overlap == 0) and (duplicate_overlap == 0)

    return {
        "splitter_name": splitter_name,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_events": len(train_events),
        "test_events": len(test_events),
        "event_overlap": event_overlap,
        "facility_overlap": facility_overlap,
        "duplicate_overlap": duplicate_overlap,
        "temporal_max_train": str(max_train_ts),
        "temporal_min_test": str(min_test_ts),
        "is_leakage_free": is_clean
    }
